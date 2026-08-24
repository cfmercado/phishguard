# PhishGuard

A Manifest V3 Gmail extension prototype that adds a phishing scan button to Gmail and sends extracted email features to a backend model for classification.

## Features

- Injects a custom toolbar button into Gmail
- Extracts email metadata and body content
- Detects phishing risk using a backend service
- Shows results in Gmail via modal dialogs
- Uses `gmail-js` for Gmail DOM/API integration

## Files

- manifest.json
  - Chrome extension manifest v3 config
  - Declares content scripts and background service worker
- background.js
  - Handles `scan_email` messages
  - Sends payload to backend model endpoint
- extensionInjector.js
  - Injects gmailJsLoader.js and extension.js
  - Bridges page messages to the background script
- gmailJsLoader.js
  - Loads `gmail-js` and initializes `window._gmailjs`
- extension.js
  - Main extension logic
  - Adds button, extracts email content, computes features, displays verdict
- style.css
  - Styling for the injected toolbar button

## Installation

```bash
npm install
```

## Build

```bash
npm run build
```

Optional development build with watch:

```bash
npm run dev
```

## Load in Chrome

1. Open `chrome://extensions`
2. Enable `Developer mode`
3. Click `Load unpacked`
4. Select the project folder

## How it works

- extensionInjector.js runs at `document_start` on Gmail
- It injects the Gmail loader and the extension code into the page
- extension.js waits for Gmail to load, then adds a toolbar button
- When clicked, it extracts:
  - subject
  - cleaned email body
  - URLs and URL metadata
  - attachment count and types
- The payload is sent through `window.postMessage` to the injector
- The injector forwards it to background.js
- background.js calls the backend API and returns the result
- The page shows a modal with:
  - phishing alert
  - safe result
  - or error message

## Backend

- Current backend URL: `https://phishguard-backend-1qg5.onrender.com/predict`
- If you want local development, update background.js to use `http://localhost:8000/predict`

## Notes

- This repo uses `gmail-js` and `jquery`
- The extension bundles gmailJsLoader.js and extension.js into dist
- manifest.json declares `web_accessible_resources` for the injected scripts