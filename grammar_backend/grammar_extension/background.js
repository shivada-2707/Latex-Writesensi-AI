chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {

  // ================= GRAMMAR CHECK (Rule-Based) =================
  if (msg.type === "GRAMMAR_CHECK") {

    fetch("http://127.0.0.1:8001/grammar/check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: msg.text })
    })
      .then(res => {
        if (!res.ok) throw new Error("Grammar backend error");
        return res.json();
      })
      .then(data => {
        console.log("Grammar Backend Response:", data);

        if (!data || !Array.isArray(data.matches)) {
          sendResponse({ matches: [] });
        } else {
          sendResponse({ matches: data.matches });
        }
      })
      .catch(err => {
        console.error("Grammar error:", err);
        sendResponse({ matches: [] });
      });

    return true;
  }


  // ================= AI GRAMMAR IMPROVE =================
  if (msg.type === "GRAMMAR_AI_IMPROVE") {

    fetch("http://127.0.0.1:8001/grammar/ai-improve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: msg.text })
    })
      .then(res => {
        if (!res.ok) throw new Error("AI grammar improve error");
        return res.json();
      })
      .then(data => {
        console.log("AI Grammar Improve Response:", data);

        if (!data || !data.improved_text) {
          sendResponse({ improved_text: null });
        } else {
          sendResponse({ improved_text: data.improved_text });
        }
      })
      .catch(err => {
        console.error("AI grammar error:", err);
        sendResponse({ improved_text: null });
      });

    return true;
  }


  // ================= CLARITY ANALYZE =================
  if (msg.type === "CLARITY_ANALYZE") {

    fetch("http://127.0.0.1:8002/clarity/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: msg.text })
    })
    .then(res => {
      if (!res.ok) throw new Error("Clarity analyze backend error");
      return res.json();
    })
    .then(data => sendResponse(data))
    .catch(err => {
      console.error("Clarity analyze error:", err);
      sendResponse({ error: true });
    });

    return true;
  }


  // ================= CLARITY ACADEMIC =================
  if (msg.type === "CLARITY_ACADEMIC") {

    fetch("http://127.0.0.1:8002/clarity/academic", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: msg.text })
    })
    .then(res => {
      if (!res.ok) throw new Error("Clarity academic backend error");
      return res.json();
    })
    .then(data => sendResponse(data))
    .catch(err => {
      console.error("Clarity academic error:", err);
      sendResponse({ error: true });
    });

    return true;
  }


  // ================= CLARITY IMPROVE =================
  if (msg.type === "CLARITY_IMPROVE") {

    fetch("http://127.0.0.1:8002/clarity/improve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: msg.text })
    })
    .then(res => {
      if (!res.ok) throw new Error("Clarity improve backend error");
      return res.json();
    })
    .then(data => sendResponse(data))
    .catch(err => {
      console.error("Clarity improve error:", err);
      sendResponse({ revised_text: null });
    });

    return true;
  }


  // ================= DOCUMENT SUMMARY =================
  if (msg.type === "DOCUMENT_SUMMARY") {

    fetch("http://127.0.0.1:8004/summary/document", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        text: msg.text
      })
    })
    .then(res => {
      if (!res.ok) throw new Error("Summary backend error");
      return res.json();
    })
    .then(data => {
      console.log("Summary Response:", data);

      if (!data || !data.section_summaries) {
        sendResponse({ section_summaries: {} });
      } else {
        sendResponse(data);
      }
    })
    .catch(err => {
      console.error("Summary error:", err);
      sendResponse({ section_summaries: {} });
    });

    return true;
  }

// ================= TRANSLATION =================
 // ================= TRANSLATION =================
  // ================= TRANSLATION =================

  if (msg.type === "TRANSLATE_TEXT") {

    fetch("http://127.0.0.1:8005/translate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        text: msg.text,
        language: msg.language
      })
    })
    .then(res => {

      if (!res.ok) {
        throw new Error("Translation backend error");
      }

      return res.json();
    })
    .then(data => {

      if (!data || !data.translation) {
        sendResponse({ translation: "Translation failed." });
        return;
      }

      sendResponse({ translation: data.translation });

    })
    .catch(err => {

      console.error("Translation error:", err);

      sendResponse({
        translation: "Translation server error."
      });

    });

    return true;
  }
});
