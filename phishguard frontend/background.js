chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "scan_email") {
        // fetch('http://localhost:8000/predict', {
        fetch('https://phishguard-backend-1qg5.onrender.com/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(request.payload)
        })
        .then(response => response.json())
        .then(data => sendResponse(data))
        .catch(error => {
            console.error("PhishGuard Backend Error:", error);
            sendResponse({ status: "error", message: error.toString()} );
        });

        // Return true tells Chrome we will send the response asynchronously
        return true;
    }
});