"use strict";

function addScript(src) {
    const script = document.createElement("script");
    script.type = "text/javascript";
    script.src = chrome.runtime.getURL(src);
    (document.body || document.head || document.documentElement).appendChild(script);
}

addScript("dist/gmailJsLoader.js");
addScript("dist/extension.js");

// Bridge between Main World and Background Worker
window.addEventListener("message", (event) => {
    // Only accept our specific PhishGuard messages
    if (event.source !== window || !event.data || event.data.type !== "PHISHGUARD_SCAN") {
        return;
    }

    // Forward the extracted email data to the Background Script
    chrome.runtime.sendMessage({ action: "scan_email", payload: event.data.data }, (response) => {
        // Send the model's verdict back to the Main World UI
        window.postMessage({ type: "PHISHGUARD_RESULT", data: response }, "*");
    });
});