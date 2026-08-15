const API_BASE = "http://127.0.0.1:8765/api/v1";

// Setup Context Menus on Install
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "recallbox-save-selection",
    title: "Save selection to RecallBox",
    contexts: ["selection"]
  });

  chrome.contextMenus.create({
    id: "recallbox-save-page",
    title: "Remember this page in RecallBox",
    contexts: ["page", "link"]
  });
});

// Handle Context Menu clicks
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === "recallbox-save-selection") {
    const selectedText = info.selectionText || "";
    const payload = {
      title: `Selection from: ${tab.title || tab.url}`,
      content: selectedText,
      source_url: tab.url,
      source_type: "quote",
      source: "extension_context_menu"
    };
    await sendMemoryToBackend(payload, tab.id);
  } else if (info.menuItemId === "recallbox-save-page") {
    const targetUrl = info.linkUrl || tab.url;
    const payload = {
      title: tab.title || targetUrl,
      source_url: targetUrl,
      source: "extension_context_menu"
    };
    await sendMemoryToBackend(payload, tab.id);
  }
});

// Handle Keyboard Shortcuts (e.g. Ctrl+Shift+R)
chrome.commands.onCommand.addListener(async (command) => {
  if (command === "quick_capture") {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab && tab.url) {
      const payload = {
        title: tab.title || tab.url,
        source_url: tab.url,
        source: "extension_shortcut"
      };
      await sendMemoryToBackend(payload, tab.id);
    }
  }
});

async function sendMemoryToBackend(payload, tabId) {
  try {
    const response = await fetch(`${API_BASE}/memories`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (response.ok) {
      flashBadge("✓", "#22c55e");
    } else {
      flashBadge("!", "#ef4444");
    }
  } catch (err) {
    console.error("Failed to connect to RecallBox local backend:", err);
    flashBadge("!", "#f59e0b");
  }
}

function flashBadge(text, color) {
  chrome.action.setBadgeText({ text: text });
  chrome.action.setBadgeBackgroundColor({ color: color });
  setTimeout(() => {
    chrome.action.setBadgeText({ text: "" });
  }, 2500);
}
