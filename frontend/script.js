const chatWindow = document.getElementById("chatWindow");
const form = document.getElementById("composerForm");
const input = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");

// Conversation history sent to the backend on every request so the LLM
// keeps context across turns (duration, follow-up answers, etc).
let history = [];
let triageCounter = 0;

function scrollToBottom() {
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function addUserMessage(text) {
  const div = document.createElement("div");
  div.className = "message user";
  div.innerHTML = `<div class="bubble"><p></p></div>`;
  div.querySelector("p").textContent = text;
  chatWindow.appendChild(div);
  scrollToBottom();
}

function addAssistantText(text) {
  const div = document.createElement("div");
  div.className = "message assistant";
  div.innerHTML = `<div class="bubble"><p></p></div>`;
  div.querySelector("p").textContent = text;
  chatWindow.appendChild(div);
  scrollToBottom();
  return div;
}

function addTypingIndicator() {
  const div = document.createElement("div");
  div.className = "message assistant";
  div.id = "typingIndicator";
  div.innerHTML = `<div class="bubble"><div class="typing-dots"><span></span><span></span><span></span></div></div>`;
  chatWindow.appendChild(div);
  scrollToBottom();
}

function removeTypingIndicator() {
  const el = document.getElementById("typingIndicator");
  if (el) el.remove();
}

function triageLabel(level) {
  if (level === "self-care") return "Self-care";
  if (level === "consult-doctor") return "Consult a doctor";
  if (level === "emergency") return "Emergency";
  return "Assessment";
}

function renderTriageCard(data) {
  triageCounter += 1;
  const level = data.triage_level || "consult-doctor";
  const idCode = `TRIAGE-${String(triageCounter).padStart(2, "0")}`;

  const wrapper = document.createElement("div");
  wrapper.className = "message assistant";

  const card = document.createElement("div");
  card.className = `triage-card ${level}`;

  card.innerHTML = `
    <div class="triage-header">
      <span class="triage-tag ${level}">${triageLabel(level)}</span>
      <span class="triage-id">${idCode}</span>
    </div>
    <h3>Assessment summary</h3>
    ${
      data.possible_conditions && data.possible_conditions.length
        ? `<div class="triage-section"><span class="label">Possible conditions</span>
           <div class="condition-chip-row" id="chipRow-${triageCounter}"></div></div>`
        : ""
    }
    <div class="triage-section"><span class="label">Advice</span><span id="advice-${triageCounter}"></span></div>
    ${
      data.medicine_category
        ? `<div class="triage-section"><span class="label">Medicine category</span><span id="med-${triageCounter}"></span></div>`
        : ""
    }
    ${
      data.reasoning
        ? `<div class="triage-section"><span class="label">Why</span><span id="reasoning-${triageCounter}"></span></div>`
        : ""
    }
    <div class="triage-disclaimer" id="disclaimer-${triageCounter}"></div>
  `;

  wrapper.appendChild(card);
  chatWindow.appendChild(wrapper);

  // Set text content safely (avoids HTML injection from LLM output)
  if (data.possible_conditions && data.possible_conditions.length) {
    const chipRow = document.getElementById(`chipRow-${triageCounter}`);
    data.possible_conditions.forEach((c) => {
      const chip = document.createElement("span");
      chip.className = "condition-chip";
      chip.textContent = c;
      chipRow.appendChild(chip);
    });
  }
  document.getElementById(`advice-${triageCounter}`).textContent = data.advice || "";
  if (data.medicine_category) {
    document.getElementById(`med-${triageCounter}`).textContent = data.medicine_category;
  }
  if (data.reasoning) {
    document.getElementById(`reasoning-${triageCounter}`).textContent = data.reasoning;
  }
  document.getElementById(`disclaimer-${triageCounter}`).textContent =
    data.disclaimer || "This is not a medical diagnosis. Please consult a doctor for confirmation.";

  scrollToBottom();
}

async function sendMessage(message) {
  addUserMessage(message);
  history.push({ role: "user", content: message });
  input.value = "";
  sendBtn.disabled = true;
  addTypingIndicator();

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history: history.slice(0, -1) }),
    });

    const data = await res.json();
    removeTypingIndicator();

    const r = data.response;

    if (data.emergency) {
      renderTriageCard({ ...r, triage_level: "emergency" });
      history.push({ role: "assistant", content: r.advice });
      return;
    }

    if (r.follow_up_question) {
      addAssistantText(r.follow_up_question);
      history.push({ role: "assistant", content: r.follow_up_question });
    } else {
      renderTriageCard(r);
      history.push({ role: "assistant", content: JSON.stringify(r) });
    }
  } catch (err) {
    removeTypingIndicator();
    addAssistantText("Something went wrong reaching the server. Make sure the backend is running.");
    console.error(err);
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  sendMessage(text);
});
