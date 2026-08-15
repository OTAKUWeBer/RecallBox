// Content script to safely extract page content and metadata
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "get_page_data") {
    try {
      const title = document.title || "";
      const ogTitle = document.querySelector('meta[property="og:title"]')?.getAttribute("content");
      const metaDesc = document.querySelector('meta[name="description"]')?.getAttribute("content") ||
                       document.querySelector('meta[property="og:description"]')?.getAttribute("content") || "";
      
      const author = document.querySelector('meta[name="author"]')?.getAttribute("content") || "";

      // Extract main readable body text without scripts/styles
      const clone = document.body.cloneNode(true);
      const scripts = clone.querySelectorAll("script, style, nav, footer, header, noscript, iframe");
      scripts.forEach(s => s.remove());
      
      const textContent = clone.innerText ? clone.innerText.slice(0, 4000) : "";
      
      // Heuristic suggested tags from page keywords & headings
      const suggestedTags = [];
      const keywordsMeta = document.querySelector('meta[name="keywords"]')?.getAttribute("content");
      if (keywordsMeta) {
        keywordsMeta.split(",").slice(0, 4).forEach(k => {
          const clean = k.trim().toLowerCase();
          if (clean && clean.length > 2) suggestedTags.push(clean);
        });
      }

      sendResponse({
        title: ogTitle || title,
        description: metaDesc,
        content: `${metaDesc}\n\n${textContent}`.trim(),
        author: author,
        suggested_tags: suggestedTags
      });
    } catch (e) {
      console.error("Error reading page data:", e);
      sendResponse({ title: document.title, content: "" });
    }
  }
  return true;
});
