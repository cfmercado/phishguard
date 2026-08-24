"use strict";

// loader-code: wait until gmailjs has finished loading, before triggering actual extensiode-code.
const loaderId = setInterval(() => {
    if (!window._gmailjs) {
        return;
    }

    clearInterval(loaderId);
    startExtension(window._gmailjs);
}, 100);

function startExtension(gmail) {
    console.log("PhishGuard loading...");
    window.gmail = gmail;

    gmail.observe.on("load", () => {
        
        // Listen for when an email is opened
        gmail.observe.on("view_email", (domEmail) => {
            if (document.querySelectorAll('.phishguard-btn').length > 0) {
                return; 
            }
            
            // Inject the scan button into the Gmail toolbar
            gmail.tools.add_toolbar_button('🛡️ Scan for Phishing', function() {
                gmail.tools.infobox('PhishGuard is analyzing...', 2000);

                // Extract the features
                const emailData = gmail.new.get.email_data(domEmail);
                const subject = emailData.subject || "no subject";
                const bodyHtml = domEmail.body() || "";

                const cleanBody = bodyHtml
                    .replace(/<[^>]*>?/gm, ' ')
                    .replace(/&[a-z0-9]+;/gi, ' ')
                    .replace(/\s+/g, ' ')
                    .trim() || "no body";
                
                const urlMatches = [...bodyHtml.matchAll(/href=["'](http[s]?:\/\/[^"']+)["']/gi)];
                const urls = urlMatches.map(m => m[1]);

                const url_count = urls.length;
                let url_length_max = 0;
                let url_length_avg = 0;
                let url_subdom_max = 0;
                let url_subdom_avg = 0;

                if (url_count > 0) {
                    const lengths = urls.map(u => u.length);
                    url_length_max = Math.max(...lengths);
                    url_length_avg = lengths.reduce((a, b) => a + b, 0) / url_count;

                    const subdomCounts = urls.map(u => {
                        try {
                            const host = new URL(u).hostname;
                            // Approximate subdomains by splitting by '.' and subtracting the root and TLD
                            return Math.max(0, host.split('.').length - 2); 
                        } catch (e) {
                            return 0; // Catch malformed URLs
                        }
                    });
                    url_subdom_max = Math.max(...subdomCounts);
                    url_subdom_avg = subdomCounts.reduce((a, b) => a + b, 0) / url_count;
                }

                const attachments = domEmail.attachments() || [];
                const attachment_count = attachments.length;
                const has_attachments = attachment_count > 0;

                const attachment_types = attachments.map(a => {
                    const parts = a.name.split('.');
                    return parts.length > 1 ? parts.pop().toLowerCase() : 'unknown';
                }).join(' ') || "none";

                const payload = {
                    subject: subject,
                    body: cleanBody,
                    url_count: url_count,
                    url_length_max: url_length_max,
                    url_length_avg: url_length_avg,
                    url_subdom_max: url_subdom_max,
                    url_subdom_avg: url_subdom_avg,
                    attachment_count: attachment_count,
                    has_attachments: has_attachments,
                    attachment_types: attachment_types
                };
                
                // Send to the Injector (which sends to Background Worker)
                window.postMessage({ type: "PHISHGUARD_SCAN", data: payload }, "*");

            }, 'phishguard-btn');
        });
    });

    // Listen for the final verdict coming back from the backend
    window.addEventListener("message", (event) => {
        if (event.source === window && event.data && event.data.type === "PHISHGUARD_RESULT") {
            const result = event.data.data;
            
            if (result.status === 'phishing') {
                const title = '⚠️ PhishGuard Security Alert';
                
                // Build the HTML content for the modal
                let contentHtml = `<div style="font-size: 14px;">`;
                contentHtml += `<p style="color: #d93025; font-weight: bold; font-size: 16px;">Phishing Detected! (Confidence: ${result.confidence}%)</p>`;
                
                if (result.reasons && result.reasons.length > 0) {
                    contentHtml += `<p>The AI model flagged this email based on the following red flags:</p><ul>`;
                    result.reasons.forEach(reason => {
                        contentHtml += `<li style="margin-bottom: 4px;"><b>${reason}</b></li>`;
                    });
                    contentHtml += `</ul>`;
                }
                
                contentHtml += `<p style="margin-top: 15px; color: #5f6368;"><i>Recommendation: Do not click any links or download attachments.</i></p>`;
                contentHtml += `</div>`;

                // Launch the modal
                gmail.tools.add_modal_window(title, contentHtml, function() {
                    // This function runs when the user clicks "OK"
                    gmail.tools.remove_modal_window();
                });
                 
            } else if (result.status === 'safe') {
                const title = '✅ PhishGuard Scan Complete';
                const contentHtml = `<p style="font-size: 14px;">This email appears safe. (Risk: ${result.confidence}%)</p>`;

                gmail.tools.add_modal_window(title, contentHtml, function() {
                    gmail.tools.remove_modal_window();
                });
                
            } else {
                const title = '❌ PhishGuard Error';
                const contentHtml = `<p>Could not reach the model server. Ensure your backend is running.</p>`;
                
                gmail.tools.add_modal_window(title, contentHtml, function() {
                    gmail.tools.remove_modal_window();
                });
            }
        }
    });
}