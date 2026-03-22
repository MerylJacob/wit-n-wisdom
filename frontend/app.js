// ─── Config ──────────────────────────────────────────────────────────────────
const API_BASE = 'http://localhost:8000';

// ─── Character state ─────────────────────────────────────────────────────────
let activeCharacter = 'austen';

const CHARACTER_META = {
  austen: { name: 'The Narrator',    welcome: 'Good day, dear reader. I am intimately acquainted with all six of Jane Austen\'s major novels. Ask me of characters, themes, plot, or society, I shall answer with fidelity to the text.' },
  darcy:  { name: 'Mr. Darcy',       welcome: 'You have a question. Ask it.' },
  emma:   { name: 'Emma Woodhouse',  welcome: 'Oh, how delightful, a question! I do so enjoy a good enquiry. I have read extensively, you know, and I am quite certain I shall be of tremendous help to you.' },
};

// ─── DOM refs ────────────────────────────────────────────────────────────────
const landingEl       = document.getElementById('landing');
const appEl           = document.getElementById('app');
const enterBtn        = document.getElementById('enterBtn');
const aboutBtn        = document.getElementById('aboutBtn');
const messagesEl      = document.getElementById('messages');
const inputEl         = document.getElementById('userInput');
const sendBtn         = document.getElementById('sendBtn');
const activeCharLabel = document.getElementById('activeCharLabel');

// ─── Character switcher ───────────────────────────────────────────────────────
document.querySelectorAll('.char-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const character = btn.dataset.character;
    if (character === activeCharacter) return;

    activeCharacter = character;
    const meta = CHARACTER_META[character];

    // Update active button styling
    document.querySelectorAll('.char-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    // Update header badge
    activeCharLabel.textContent = meta.name;

    // Add a system message showing the character switch
    appendCharacterSwitch(meta.name);

    // Post a welcome message from the new character
    appendBotMessage(`<em>${meta.welcome}</em>`, meta.name);
  });
});

function appendCharacterSwitch(name) {
  const div = document.createElement('div');
  div.className = 'character-switch-notice';
  div.innerHTML = `<span>✦</span> Now speaking with <strong>${name}</strong> <span>✦</span>`;
  messagesEl.appendChild(div);
  scrollToBottom();
}


function goToChat() {
  landingEl.classList.add('fade-out');
  setTimeout(() => {
    landingEl.style.display = 'none';
    appEl.classList.remove('hidden');
    inputEl.focus();
  }, 700);
}

const enterBtn2 = document.getElementById('enterBtn2');
enterBtn.addEventListener('click', goToChat);
if (enterBtn2) enterBtn2.addEventListener('click', goToChat);

// ─── Chat → Landing (back button) ────────────────────────────────────────────
aboutBtn.addEventListener('click', () => {
  appEl.classList.add('hidden');
  landingEl.style.display = 'flex';
  // Small delay to allow display:flex to paint before removing fade-out
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      landingEl.classList.remove('fade-out');
    });
  });
});

// ─── Auto-resize textarea ────────────────────────────────────────────────────
inputEl.addEventListener('input', () => {
  inputEl.style.height = 'auto';
  inputEl.style.height = Math.min(inputEl.scrollHeight, 120) + 'px';
});

// ─── Send on Enter (Shift+Enter = newline) ───────────────────────────────────
inputEl.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleSend();
  }
});

sendBtn.addEventListener('click', handleSend);

// ─── Suggested question buttons ──────────────────────────────────────────────
document.querySelectorAll('.suggestion-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    inputEl.value = btn.dataset.q;
    inputEl.style.height = 'auto';
    inputEl.style.height = Math.min(inputEl.scrollHeight, 120) + 'px';
    handleSend();
  });
});

// ─── Main send handler ────────────────────────────────────────────────────────
async function handleSend() {
  const question = inputEl.value.trim();
  if (!question || sendBtn.disabled) return;

  inputEl.value = '';
  inputEl.style.height = 'auto';

  appendUserMessage(question);

  sendBtn.disabled = true;
  inputEl.disabled = true;

  const botEl = appendBotMessage('', CHARACTER_META[activeCharacter].name);
  const textEl = botEl.querySelector('.message-text');
  textEl.classList.add('streaming-cursor');

  try {
    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, character: activeCharacter }),
    });

    if (!response.ok) throw new Error(`Server error: ${response.status}`);

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let fullText = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      fullText += decoder.decode(value, { stream: true });
      textEl.innerHTML = formatText(fullText);
      scrollToBottom();
    }

  } catch (err) {
    console.error(err);
    textEl.innerHTML = `<span class="error-text">Alas, a connection error occurred. Please ensure the API server is running at ${API_BASE} and try again.</span>`;
  } finally {
    textEl.classList.remove('streaming-cursor');
    sendBtn.disabled = false;
    inputEl.disabled = false;
    inputEl.focus();
    scrollToBottom();
  }
}

// ─── Append user bubble ───────────────────────────────────────────────────────
function appendUserMessage(text) {
  const div = document.createElement('div');
  div.className = 'message user-message';
  div.innerHTML = `
    <div class="message-avatar">Y</div>
    <div class="message-body">
      <div class="message-sender">Your Enquiry</div>
      <div class="message-text">${escapeHtml(text)}</div>
    </div>`;
  messagesEl.appendChild(div);
  scrollToBottom();
}

// ─── Append bot bubble ────────────────────────────────────────────────────────
function appendBotMessage(text, senderName) {
  const name = senderName || CHARACTER_META[activeCharacter].name;
  const div = document.createElement('div');
  div.className = 'message bot-message';
  div.innerHTML = `
    <div class="message-avatar">W</div>
    <div class="message-body">
      <div class="message-sender">${name}</div>
      <div class="message-text">${text}</div>
    </div>`;
  messagesEl.appendChild(div);
  scrollToBottom();
  return div;
}

// ─── Format streamed text into HTML ──────────────────────────────────────────
function formatText(raw) {
  const paragraphs = raw.split(/\n\n+/).map(p => p.trim()).filter(Boolean);
  if (!paragraphs.length) return escapeHtml(raw);

  return paragraphs.map(p => {
    const lines = p.split('\n').map(escapeHtml).join('<br/>');
    // [Passage N — Novel Title]
    const withBadges = lines.replace(
      /\[Passage\s*(\d+)\s*[—\-]\s*([^\]]+)\]/gi,
      (_, num, title) => `<span class="source-badge">Passage ${num} &middot; ${escapeHtml(title.trim())}</span>`
    );
    // Plain [Passage N]
    const withPlain = withBadges.replace(
      /\[Passage\s*(\d+)\]/gi,
      '<span class="source-badge">Passage $1</span>'
    );
    return `<p>${withPlain}</p>`;
  }).join('');
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function scrollToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}