const API_URL = "http://127.0.0.1:8765/api/v1/memories";

document.addEventListener("DOMContentLoaded", async () => {
  const titleInput = document.getElementById("page-title");
  const urlInput = document.getElementById("page-url");
  const whyInput = document.getElementById("user-why");
  const tagsInput = document.getElementById("tags-input");
  const remindCheckbox = document.getElementById("remind-me");
  const saveBtn = document.getElementById("save-btn");
  const saveBtnText = document.getElementById("save-btn-text");
  const messageBar = document.getElementById("message-bar");
  const suggestedTagsContainer = document.getElementById("suggested-tags");

  let pageData = {
    url: "",
    title: "",
    content: "",
    author: "",
    favicon: ""
  };

  // Get active tab info and request content from content script
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab) {
      pageData.url = tab.url;
      pageData.title = tab.title || "";
      urlInput.value = tab.url;
      titleInput.value = tab.title || "";

      // Try communicating with content script
      try {
        const response = await chrome.tabs.sendMessage(tab.id, { action: "get_page_data" });
        if (response) {
          pageData = { ...pageData, ...response };
          if (response.title) titleInput.value = response.title;
          if (response.suggested_tags) {
            renderSuggestedTags(response.suggested_tags);
          }
        }
      } catch (err) {
        // Content script might not be injected in restricted URLs
      }
    }
  } catch (err) {
    console.error("Error querying active tab:", err);
  }

  function renderSuggestedTags(tags) {
    suggestedTagsContainer.innerHTML = "";
    tags.forEach(tag => {
      const chip = document.createElement("span");
      chip.className = "tag-chip";
      chip.textContent = `+ ${tag}`;
      chip.addEventListener("click", () => {
        const current = tagsInput.value.split(",").map(t => t.trim()).filter(Boolean);
        if (!current.includes(tag)) {
          current.push(tag);
          tagsInput.value = current.join(", ");
        }
      });
      suggestedTagsContainer.appendChild(chip);
    });
  }

  async function handleSave() {
    saveBtn.disabled = true;
    saveBtnText.textContent = "Remembering...";
    messageBar.className = "message-bar hidden";

    const tags = tagsInput.value.split(",").map(t => t.trim()).filter(Boolean);
    const why = whyInput.value.trim();
    const title = titleInput.value.trim() || pageData.title;

    let remindDate = null;
    if (remindCheckbox.checked) {
      const d = new Date();
      d.setDate(d.getDate() + 3); // Default 3-day reminder
      remindDate = d.toISOString();
    }

    const payload = {
      title: title,
      source_url: pageData.url,
      content: pageData.content || "",
      user_why: why || null,
      tags: tags,
      source: "extension",
      remind_at: remindDate
    };

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        messageBar.textContent = "✓ Remembered to RecallBox!";
        messageBar.className = "message-bar success";
        setTimeout(() => window.close(), 1200);
      } else {
        const errText = await response.text();
        messageBar.textContent = `Save failed: ${errText}`;
        messageBar.className = "message-bar error";
        saveBtn.disabled = false;
        saveBtnText.textContent = "Save to Memory";
      }
    } catch (e) {
      messageBar.textContent = "Cannot connect to RecallBox local backend (127.0.0.1:8765)";
      messageBar.className = "message-bar error";
      saveBtn.disabled = false;
      saveBtnText.textContent = "Save to Memory";
    }
  }

  saveBtn.addEventListener("click", handleSave);

  // Keyboard shortcut Enter on input fields saves immediately
  document.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey && e.target.tagName !== "TEXTAREA") {
      handleSave();
    }
  });

  whyInput.focus();
});
