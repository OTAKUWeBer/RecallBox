# RecallBox Browser Extension Guide

The **RecallBox Browser Extension** allows 1-click capture from any Chromium browser (Chrome, Brave, Edge, Arc).

---

## 1. Installation (Developer Mode)

1. Open your browser and navigate to `chrome://extensions/` (or `brave://extensions/`, `edge://extensions/`).
2. Enable **Developer mode** (toggle in the top right).
3. Click **Load unpacked**.
4. Select the directory:
   ```
   recallbox/apps/extension
   ```
5. Pin the **RecallBox** extension to your toolbar.

---

## 2. Capture Workflows

### A. 1-Click Page Capture
Click the RecallBox extension icon on any webpage to open the minimal popup:
- **Title**: Pre-filled from the page title.
- **Why are you saving this?**: Add an optional one-line intent note (`try this later`, `check benchmarks`, `reference for project`).
- **Tags**: Pre-populated with heuristic suggestions or custom tags.
- **Remind me**: Toggle a 3-day reminder.
- Press **Enter** or click **Save to Memory**.

### B. Right-Click Context Menu Selection
- Highlight any interesting paragraph, command, or code snippet on a webpage.
- Right-click and choose **"Save selection to RecallBox"**.
- The snippet, page title, URL, and timestamp are saved immediately in the background.

### C. Keyboard Shortcut (`Ctrl+Shift+R` / `Cmd+Shift+R`)
- Press `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (macOS) on any tab to save the active page instantaneously.
- The extension badge flashes a green **✓** upon successful storage.
