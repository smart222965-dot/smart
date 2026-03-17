function addMessage(sender, text, isError = false) {
  const chatBox = document.getElementById('chat-box');
  const div = document.createElement('div');
  div.className = 'message ' + (sender === 'user' ? 'user' : 'agent');
  div.innerHTML = sender === 'user' ? text : `<strong>OpenClaw:</strong> ${text.replace(/\n/g, '<br>')}`;
  if (isError) div.style.color = '#d00';
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

async function fetchStatus() {
  try {
    const r = await fetch('/status');
    const data = await r.json();
    document.getElementById('status').innerHTML =
      'Backend Status: ' + data.message +
      ' | Server: ' + data.server_host + ':' + data.server_port +
      ' | LLM: ' + data.llm.provider + ':' + data.llm.model_name;
  } catch (e) {
    document.getElementById('status').innerText = 'Status fetch failed';
  }
}

async function fetchHistory() {
  try {
    const r = await fetch('/history');
    const data = await r.json();
    displayHistory(data.logs);
  } catch (e) {
    console.error('History fetch error', e);
  }
}

function displayHistory(logs) {
  const list = document.getElementById('history-list');
  list.innerHTML = '';
  if (!logs || logs.length === 0) {
    list.innerHTML = '<li>No history yet.</li>';
    return;
  }
  logs.forEach(log => {
    const li = document.createElement('li');
    li.innerHTML = `
      <strong>User:</strong> ${log.user_text?.substring(0, 60)}<br>
      <strong>Agent:</strong> ${log.ai_response?.substring(0, 120) ?? 'N/A'}<br>
      ${log.action_performed ? `<strong>Action:</strong> ${log.action_performed} (${log.action_result ?? ''})<br>` : ''}
      <em>${new Date(log.timestamp).toLocaleString()}</em>
    `;
    list.appendChild(li);
  });
}

async function sendMessage() {
  const input = document.getElementById('user-input');
  const text = input.value.trim();
  if (!text) return;
  addMessage('user', text);
  input.value = '';

  try {
    const resp = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: text, session_id: 'default_session' })
    });
    const data = await resp.json();
    if (resp.ok) {
      let agentText = data.agent_response || 'No response';
      if (data.action_performed) {
        agentText += `\n(Action: ${data.action_performed})`;
        if (data.action_result) agentText += `\nResult: ${data.action_result}`;
      }
      addMessage('agent', agentText);
    } else {
      addMessage('agent', 'Error: ' + (data.detail || 'Unknown error'), true);
    }
  } catch (e) {
    addMessage('agent', 'Error communicating with backend: ' + e.message, true);
  }

  fetchHistory();
}

document.addEventListener('DOMContentLoaded', () => {
  fetchStatus();
  fetchHistory();
  document.getElementById('user-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
});
