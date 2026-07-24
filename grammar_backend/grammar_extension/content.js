// ================= UTILITY =================

function getSelectedTextAndRange() {
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) {
    return { text: "", apply: () => {} };
  }

  const range = selection.getRangeAt(0);
  const text = selection.toString();

  return {
    text,
    apply: (newText) => {
      range.deleteContents();
      range.insertNode(document.createTextNode(newText));
    }
  };
}

function showPopup(html) {

  const old = document.getElementById("writesense-dock");
  if (old) old.remove();

  // Inject CSS once
  if (!document.getElementById("writesense-style")) {
    const style = document.createElement("style");
    style.id = "writesense-style";
    style.innerHTML = `
      #writesense-dock {
        position: fixed;
        top: 0;
        right: 0;
        width: 420px;
        height: 100vh;
        background: #F8FAFC;
        border-left: 1px solid #E2E8F0;
        box-shadow: -6px 0 20px rgba(0,0,0,0.08);
        z-index: 999999;
        display: flex;
        flex-direction: column;
        font-family: 'Segoe UI', sans-serif;
      }

      .ws-header {
        padding: 18px;
        border-bottom: 1px solid #E2E8F0;
        background: white;
      }

      .ws-title {
        font-size: 18px;
        font-weight: 600;
        color: #1E293B;
      }

      .ws-subtitle {
        font-size: 12px;
        color: #64748B;
      }

      .ws-content {
        padding: 18px;
        overflow-y: auto;
        flex: 1;
        font-size: 13px;
        color: #334155;
      }

      .ws-section {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 14px;
        margin-bottom: 14px;
      }

      .ws-section h3 {
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 8px;
        color: #1E293B;
      }

      .ws-card {
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 8px;
        background: #FFFFFF;
      }

      .ws-button {
        background: #2563EB;
        color: white;
        border: none;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 13px;
        cursor: pointer;
        margin-right: 8px;
      }
      
      #writesense-dock input,
      #writesense-dock select {
        background: #FFFFFF !important;
        color: #1E293B !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 6px !important;
        padding: 6px 8px !important;
        font-size: 13px !important;
}

#writesense-dock input[type="radio"] {
  accent-color: #2563EB !important;
}

      .ws-button-secondary {
        background: #E2E8F0;
        color: #1E293B;
        border: none;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 13px;
        cursor: pointer;
      }

      .ws-textarea {
        width: 100%;
        height: 120px;
        border: 1px solid #CBD5E1;
        border-radius: 6px;
        padding: 10px;
        font-size: 13px;
        resize: vertical;

        background: #FFFFFF !important;
        color: #1E293B !important;
        box-shadow: none !important;
    }

      .ws-metric {
        display: flex;
        justify-content: space-between;
        padding: 6px 0;
        border-bottom: 1px solid #F1F5F9;
      }

      .ws-metric:last-child {
        border-bottom: none;
      }

      .ws-badge {
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
      }

      .ws-green { background:#DCFCE7; color:#166534; }
      .ws-orange { background:#FEF3C7; color:#92400E; }
      .ws-red { background:#FEE2E2; color:#991B1B; }

      .ws-close {
        float:right;
        cursor:pointer;
        font-size:16px;
        color:#64748B;
      }
    `;
    document.head.appendChild(style);
  }

  const dock = document.createElement("div");
  dock.id = "writesense-dock";

  dock.innerHTML = `
    <div class="ws-header">
      <span class="ws-close" id="ws-close">✕</span>
      <div class="ws-title">WriteSense AI</div>
      <div class="ws-subtitle">from draft to distiction</div>
    </div>
    <div class="ws-content" id="writesense-content">
      ${html}
    </div>
  `;

  document.body.appendChild(dock);

  document.getElementById("ws-close").onclick = closePopup;
}

function closePopup() {
  const dock = document.getElementById("writesense-dock");
  if (dock) dock.remove();
}

function makeDraggable(element, handle) {
  let offsetX = 0, offsetY = 0, isDown = false;

  handle.onmousedown = function(e) {
    isDown = true;
    offsetX = e.clientX - element.offsetLeft;
    offsetY = e.clientY - element.offsetTop;

    document.onmousemove = function(e) {
      if (!isDown) return;
      element.style.left = (e.clientX - offsetX) + "px";
      element.style.top = (e.clientY - offsetY) + "px";
      element.style.right = "auto";
    };

    document.onmouseup = function() {
      isDown = false;
      document.onmousemove = null;
      document.onmouseup = null;
    };
  };
}



// ================= FLOATING TOOLBAR =================

const writesenseToolbar = document.createElement("div");

writesenseToolbar.style.cssText = `
position:fixed;
right:20px;
bottom:20px;
display:flex;
flex-direction:column;
gap:10px;
z-index:999999;
`;

document.body.appendChild(writesenseToolbar);


// Professional button creator
function styleToolButton(btn, color){

btn.style.cssText = `
padding:10px 16px;
border:none;
border-radius:10px;
font-weight:600;
font-size:13px;
cursor:pointer;
color:white;
background:${color};
box-shadow:0 4px 12px rgba(0,0,0,0.15);
transition:all 0.2s ease;
`;

btn.onmouseenter = () => {
btn.style.transform="translateY(-2px)";
btn.style.boxShadow="0 6px 16px rgba(0,0,0,0.25)";
};

btn.onmouseleave = () => {
btn.style.transform="translateY(0px)";
btn.style.boxShadow="0 4px 12px rgba(0,0,0,0.15)";
};

writesenseToolbar.appendChild(btn);

}

// ================= GRAMMAR =================

const grammarBtn = document.createElement("button");
grammarBtn.innerText = "Grammar";
styleToolButton(grammarBtn, "#475569");

grammarBtn.onclick = () => {
  const sel = getSelectedTextAndRange();
  if (!sel.text) return alert("Select text first");

  Promise.all([

    // Rule-based grammar
    fetch("http://127.0.0.1:8001/grammar/check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: sel.text })
    }).then(res => res.json()),

    // AI grammar
    fetch("http://127.0.0.1:8001/grammar/ai-improve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: sel.text })
    }).then(res => res.json())

  ])
  .then(([ruleData, aiData]) => {

    const matches = ruleData.matches || [];
    const aiCorrected = aiData.improved_text || sel.text;
    // This is the word-by-word differences detected in backend.
    const aiChanges = aiData.ai_changes || [];

    let correctedByRules = sel.text;
//This block:
// Takes all grammar mistakes
// Removes those without suggestions
//Sorts them safely
// Replaces wrong words with correct words
// Creates a corrected paragraph
    matches
      .filter(m => m.replacement)
      .sort((a, b) => b.offset - a.offset)
      .forEach(m => {
        correctedByRules =
          correctedByRules.slice(0, m.offset) +
          m.replacement +
          correctedByRules.slice(m.offset + m.length);
      });

    let html = "";

    // =====================================================
    // RULE-BASED SECTION
    // =====================================================
//This is just layout
    html += `
      <div class="ws-section">
        <h3>Rule-Based Grammar (LanguageTool)</h3>
    `;

    if (!matches.length) {

      html += `
        <div class="ws-card">
          No rule-based grammar issues detected.
        </div>
      `;

    } else {

      matches.forEach(m => {
        html += `
          <div class="ws-card">
            <b style="color:#DC2626;">${m.error_word}</b><br><br>
            ${m.message}<br><br>
            <b>Suggestion:</b> ${m.replacement || "No automatic fix"}
          </div>
        `;
      });

      html += `
        <br>
        <b>Rule Corrected Version</b><br><br>
        <textarea id="ruleTextarea" class="ws-textarea">${correctedByRules}</textarea>
        <br><br>
        <button class="ws-button" id="applyRules">Apply Rule Fixes</button>
      `;
    }

    html += `</div>`; // Close Rule Section



    // =====================================================
    // AI STRUCTURAL SECTION.DISPLAY
    // =====================================================

    html += `
      <div class="ws-section">
        <h3>AI Structural Correction (LLaMA)</h3>
    `;

    if (aiChanges.length > 0) {

      html += `<b>AI Detected Changes</b><br><br>`;

      aiChanges.forEach(change => {
        html += `
          <div class="ws-card">
            <b style="color:#DC2626;">${change.error_word}</b><br>
            →
            <b style="color:#16A34A;">${change.correction}</b>
          </div>
        `;
      });

      html += `<br>`;

    } else {

      html += `
        <div class="ws-card">
          No structural changes detected by AI.
        </div>
      `;
    }

    html += `
      <br>
      <b>AI Improved Version</b><br><br>
      <textarea id="aiTextarea" class="ws-textarea">${aiCorrected}</textarea>
      <br><br>
      <button class="ws-button" id="applyAI">Apply AI Fix</button>
      <button class="ws-button-secondary" id="close">Close</button>
    `;

    html += `</div>`; // Close AI Section


    // Show upgraded dock panel
    showPopup(html);



    // =====================================================
    // APPLY RULE FIX
    // =====================================================
// the part that actually replaces the text inside Overleaf.
    const applyRulesBtn = document.getElementById("applyRules");
    if (applyRulesBtn) {
      applyRulesBtn.onclick = () => {
        const text = document.getElementById("ruleTextarea").value;
        // sel The selected text and The exact position of that text in Overleaf
        sel.apply(text);
        closePopup();
      };
    }


    // =====================================================
    // APPLY AI FIX
    // =====================================================

    document.getElementById("applyAI").onclick = () => {

      let text = document.getElementById("aiTextarea").value.trim();

      // Safety cleaning
      text = text.replace(/^Here is the corrected sentence:\s*/i, "");
      text = text.replace(/^Corrected sentence:\s*/i, "");
      text = text.replace(/^The corrected sentence is:\s*/i, "");
      text = text.replace(/\n+/g, "\n").trim();

      sel.apply(text);
      closePopup();
    };

    document.getElementById("close").onclick = closePopup;

  })
  .catch(() => {
    alert("Grammar system failed");
  });
};




// ================= Academic Badge =================

function getAcademicBadge(text) {

  let color = "#4CAF50";

  if (text.includes("Too simple")) color = "#ff9800";
  if (text.includes("Extremely dense")) color = "#f44336";

  return `
    <div style="
      padding:8px;
      border-radius:6px;
      background:${color};
      color:white;
      font-weight:bold;
      text-align:center;
      margin-top:5px;
    ">
      ${text}
    </div>
  `;
}


// ================= CLARITY =================

// ================= CLARITY =================

const clarityBtn = document.createElement("button");
clarityBtn.innerText = "Clarity";
styleToolButton(clarityBtn, "#475569");
clarityBtn.onclick = () => {

  const sel = getSelectedTextAndRange();
  if (!sel.text) return alert("Select text first");

  chrome.runtime.sendMessage(
    { type: "CLARITY_ANALYZE", text: sel.text },
    (res) => {

      // Call this URL → FastAPI
    
    if (!res || !res.metrics || !res.ai_evaluation) {
        alert("Clarity analysis failed");
        return;
      }

      const m = res.metrics;
      const ai = res.ai_evaluation;

      chrome.runtime.sendMessage(
        { type: "CLARITY_ACADEMIC", text: sel.text },
        (academicRes) => {

          if (!academicRes || !academicRes.metrics) {
            alert("Academic metrics failed");
            return;
          }

          const am = academicRes.metrics;

          let html = "";

          // READABILITY
          html += `
            <div class="ws-section">
              <h3>Readability Metrics</h3>

              <div class="ws-metric">
                <span>Flesch Reading Ease</span>
                <span>${m.flesch_reading_ease}</span>
              </div>

              <div style="font-size:12px;color:#64748B;margin-bottom:10px;">
                ${m.reading_ease_explanation}
              </div>

              <div class="ws-metric">
                <span>Flesch–Kincaid Grade</span>
                <span>${m.flesch_kincaid_grade}</span>
              </div>

              <div style="margin-top:8px;">
                ${getAcademicBadge(m.academic_suitability)}
              </div>
            </div>
          `;

          // AI STRUCTURE
          html += `
            <div class="ws-section">
              <h3>AI Structural Evaluation</h3>

              <div class="ws-metric">
                <span>Structure Quality</span>
                <span>${ai.structure_quality}</span>
              </div>

              <div style="font-size:12px;color:#64748B;margin-bottom:10px;">
                ${ai.structure_reason}
              </div>

              <div class="ws-metric">
                <span>Tone Quality</span>
                <span>${ai.tone_quality}</span>
              </div>

              <div style="font-size:12px;color:#64748B;">
                ${ai.tone_reason}
              </div>
            </div>
          `;

          // ACADEMIC METRICS
          html += `
            <div class="ws-section">
              <h3>Academic Structural Metrics</h3>

              <div class="ws-metric">
                <span>Passive Voice</span>
                <span>${am.passive_voice_percent}%</span>
              </div>
              <div style="font-size:12px;color:#64748B;margin-bottom:8px;">
                ${am.passive_interpretation}
              </div>

              <div class="ws-metric">
                <span>Lexical Density</span>
                <span>${am.lexical_density_percent}%</span>
              </div>
              <div style="font-size:12px;color:#64748B;margin-bottom:8px;">
                ${am.lexical_density_interpretation}
              </div>

              <div class="ws-metric">
                <span>Clause Density</span>
                <span>${am.clause_density}</span>
              </div>
              <div style="font-size:12px;color:#64748B;margin-bottom:8px;">
                ${am.clause_density_interpretation}
              </div>

              <div class="ws-metric">
                <span>Nominalization Ratio</span>
                <span>${am.nominalization_ratio_percent}%</span>
              </div>
              <div style="font-size:12px;color:#64748B;">
                ${am.nominalization_interpretation}
              </div>
            </div>
          `;

          // IMPROVEMENT ADVICE (No Enhance Button)
          html += `
            <div class="ws-section">
              <h3>Improvement Advice</h3>
              <div style="font-size:13px;">
                ${ai.improvement_advice}
              </div>
              <br>
              <button class="ws-button-secondary" id="close">Close</button>
            </div>
          `;

          showPopup(html);

          document.getElementById("close").onclick = closePopup;
        }
      );
    }
  );
};


// ================= RESEARCH PAPERS =================

function getFullDocumentText() {

  const editor = document.querySelector(".cm-content");

  if (!editor) return "";

  return editor.innerText;
}

const researchBtn = document.createElement("button");
researchBtn.innerText = "📚 Papers";
styleToolButton(researchBtn, "#475569");

researchBtn.onclick = () => {

  const fullText = getFullDocumentText();
// Extract abstract or fallback text.
  if (!fullText) {
    alert("Unable to read full document");
    return;
  }

  showPopup(`
    <b>Research Paper Filter</b><br><br>

    <label>
      <input type="radio" name="yearMode" value="range" checked>
      Year Range
    </label><br>
    From: <input type="number" id="yearFrom" value="2020" style="width:80px;">
    To: <input type="number" id="yearTo" value="2025" style="width:80px;"><br><br>

    <label>
      <input type="radio" name="yearMode" value="single">
      Single Year
    </label><br>
    Year: <input type="number" id="singleYear" value="2024" style="width:80px;"><br><br>

    <button id="searchPapers">Search</button>
  `);

  document.getElementById("searchPapers").onclick = () => {

    const mode = document.querySelector('input[name="yearMode"]:checked').value;

    let year_from, year_to;

    if (mode === "range") {
      year_from = parseInt(document.getElementById("yearFrom").value);
      year_to = parseInt(document.getElementById("yearTo").value);
    } else {
      const single = parseInt(document.getElementById("singleYear").value);
      year_from = single;
      year_to = single;
    }

    document.getElementById("writesense-content").innerHTML =
      "<b>Analyzing document and searching papers...</b>";

    fetch("http://127.0.0.1:8003/research/find", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: fullText,
        year_from: year_from,
        year_to: year_to
      })
    })
    .then(res => res.json())
    .then(data => {

      let html = `
        <b>Document Analysis</b><br><br>

        <b>Primary Domain:</b> ${data.analysis.primary_domain}<br><br>

        <b>Sub Domains:</b><br>
        ${data.analysis.sub_domains.map(d => "• " + d).join("<br>")}
        <br><br>

        <b>Extracted Keywords:</b><br>
        ${data.analysis.keywords.map(k => "• " + k).join("<br>")}
        <br><br>

        <hr>

        <b>Related Research Papers</b><br><br>
        <b>Year Filter:</b> ${year_from} - ${year_to}<br><br>
      `;

      if (!data.related_papers.length) {
        html += "<b>No relevant papers found.</b>";
      }

      data.related_papers.forEach((p, i) => {

        html += `
          <hr>
          <b>${i + 1}. ${p.title}</b><br>
          ${p.authors.join(", ")} (${p.year})<br>
          <a href="${p.url}" target="_blank">Open Paper</a><br><br>

          <b>Citation (IEEE):</b><br>
          <textarea readonly style="
            width:100%;
            height:70px;
            background:#1c1c1c;
            color:white;
            border:1px solid #444;
            padding:8px;
            resize:none;
          " onclick="this.select()">${p.ieee_citation}</textarea><br><br>
        `;
      });

      document.getElementById("writesense-content").innerHTML = html;
    })
    .catch(() => {
      document.getElementById("writesense-content").innerHTML =
        "<b>Failed to fetch research papers</b>";
    });
  };
};





// ================= DOCUMENT SUMMARY =================
// ================= DOCUMENT SUMMARY =================
const summaryBtn = document.createElement("button");
summaryBtn.innerText = "Summary";
styleToolButton(summaryBtn, "#475569");

summaryBtn.onclick = () => {

  const selection = window.getSelection().toString().trim();

  if (!selection) {
    alert("Please select text to summarize.");
    return;
  }

  showPopup("<b>Generating summary...</b>");

  chrome.runtime.sendMessage(
    {
      type: "DOCUMENT_SUMMARY",
      text: selection
    },
    (res) => {

      if (!res || !res.section_summaries) {
        document.getElementById("writesense-content").innerHTML =
          "<b>Summary generation failed.</b>";
        return;
      }

      const summary = res.section_summaries.Summary || "Summary unavailable.";

      let html = `
<div class="ws-section">
  <h3>Summary</h3>
  <textarea class="ws-textarea" readonly>${summary}</textarea>
</div>
`;

      document.getElementById("writesense-content").innerHTML = html;
    }
  );
};



// ================= TRANSLATION BUTTON =================

const translateBtn = document.createElement("button");
translateBtn.innerText = "Translate";

styleToolButton(translateBtn, "#475569");


// ================= SAFE TEXT SELECTION =================

function getSelectedTextSafe() {

  const selection = window.getSelection();

  if (!selection || selection.rangeCount === 0) {
    return "";
  }

  let text = selection.toString();

  // Normalize spaces
  text = text.replace(/\s+/g, " ").trim();

  // Remove duplicate blocks
  const blocks = text.split(/\n+/);

  const seen = new Set();
  const cleaned = [];

  for (let block of blocks) {

    const clean = block.trim();

    if (clean.length < 5) continue;

    if (!seen.has(clean)) {
      seen.add(clean);
      cleaned.push(clean);
    }

  }

  text = cleaned.join(" ");

  // Prevent extremely long text
  if (text.length > 2000) {
    text = text.slice(0, 2000);
  }

  return text;
}


// ================= BUTTON CLICK =================

translateBtn.onclick = () => {

  const selectedText = getSelectedTextSafe();

  if (!selectedText) {
    alert("Select text first");
    return;
  }

  showPopup(`
    <div class="ws-section">

      <h3>Multilingual Translation</h3>

      <select id="targetLang" style="width:100%;padding:6px;margin-bottom:10px;">
        <option value="Malayalam">Malayalam</option>
        <option value="Hindi">Hindi</option>
        <option value="Tamil">Tamil</option>
        <option value="Telugu">Telugu</option>
        <option value="Kannada">Kannada</option>
        <option value="Bengali">Bengali</option>
        <option value="Marathi">Marathi</option>
        <option value="Gujarati">Gujarati</option>
        <option value="Punjabi">Punjabi</option>
        <option value="Urdu">Urdu</option>
        <option value="French">French</option>
        <option value="German">German</option>
        <option value="Spanish">Spanish</option>
        <option value="Italian">Italian</option>
        <option value="Portuguese">Portuguese</option>
        <option value="Dutch">Dutch</option>
        <option value="Greek">Greek</option>
        <option value="Polish">Polish</option>
        <option value="Czech">Czech</option>
        <option value="Romanian">Romanian</option>
        <option value="Russian">Russian</option>
        <option value="Ukrainian">Ukrainian</option>
        <option value="Chinese">Chinese</option>
        <option value="Japanese">Japanese</option>
        <option value="Korean">Korean</option>
        <option value="Thai">Thai</option>
        <option value="Vietnamese">Vietnamese</option>
        <option value="Indonesian">Indonesian</option>
        <option value="Malay">Malay</option>
        <option value="Arabic">Arabic</option>
        <option value="Hebrew">Hebrew</option>
        <option value="Turkish">Turkish</option>
        <option value="Persian">Persian</option>
        <option value="Swahili">Swahili</option>
        <option value="Zulu">Zulu</option>
      </select>

      <button class="ws-button" id="translateNow">Translate</button>

      <br><br>

      <textarea
        id="translationOutput"
        class="ws-textarea"
        readonly
        style="height:160px"
      ></textarea>

      <br>

      <button class="ws-button-secondary" id="closeTranslation">
        Close
      </button>

    </div>
  `);


  const translateNowBtn = document.getElementById("translateNow");
  const closeBtn = document.getElementById("closeTranslation");


  translateNowBtn.onclick = () => {

    const language = document.getElementById("targetLang").value;

    const output = document.getElementById("translationOutput");

    output.value = "Translating...";

    chrome.runtime.sendMessage(
      {
        type: "TRANSLATE_TEXT",
        text: selectedText,
        language: language
      },
      (res) => {

        if (chrome.runtime.lastError) {
          output.value = "Extension error.";
          return;
        }

        if (!res || !res.translation) {
          output.value = "Translation failed.";
          return;
        }

        output.value = res.translation;

      }
    );

  };


  closeBtn.onclick = closePopup;

};


