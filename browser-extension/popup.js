const backendUrlInput = document.getElementById("backendUrl");
const leetcodeUsernameInput = document.getElementById("leetcodeUsername");
const statusEl = document.getElementById("status");

function backendUrl() {
  return backendUrlInput.value.trim().replace(/\/$/, "");
}

function setStatus(message) {
  statusEl.textContent = message;
}

async function loadSettings() {
  const { backendUrl: savedBackendUrl, leetcodeUsername } = await chrome.storage.sync.get([
    "backendUrl",
    "leetcodeUsername",
  ]);
  backendUrlInput.value = savedBackendUrl || "http://localhost:8000";
  leetcodeUsernameInput.value = leetcodeUsername || "";
}

async function saveSettings() {
  await chrome.storage.sync.set({
    backendUrl: backendUrl(),
    leetcodeUsername: leetcodeUsernameInput.value.trim(),
  });
  setStatus("Settings saved.");
}

async function captureLeetCodeSession() {
  await saveSettings();
  const username = leetcodeUsernameInput.value.trim();
  if (!backendUrl() || !username) {
    setStatus("Set a backend URL and LeetCode username first.");
    return;
  }

  const cookie = await chrome.cookies.get({ url: "https://leetcode.com", name: "LEETCODE_SESSION" });
  if (!cookie || !cookie.value) {
    setStatus("No LEETCODE_SESSION cookie found. Log in to LeetCode first.");
    return;
  }

  const response = await fetch(`${backendUrl()}/auth/leetcode/connect`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, session_cookie: cookie.value }),
  });

  if (!response.ok) {
    setStatus(`Backend rejected the connection: ${response.status}`);
    return;
  }

  setStatus("LeetCode session captured and stored.");
}

async function connectGitHub() {
  await saveSettings();
  if (!backendUrl()) {
    setStatus("Set a backend URL first.");
    return;
  }

  const startResponse = await fetch(`${backendUrl()}/auth/github/device/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });

  if (!startResponse.ok) {
    setStatus(`Could not start GitHub login: ${startResponse.status}`);
    return;
  }

  const startData = await startResponse.json();
  const verificationUrl = startData.verification_uri_complete || startData.verification_uri;
  setStatus(`Open ${verificationUrl}\nCode: ${startData.user_code}\nWaiting for approval...`);

  if (verificationUrl) {
    await chrome.tabs.create({ url: verificationUrl });
  }

  const completeResponse = await fetch(`${backendUrl()}/auth/github/device/complete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      device_code: startData.device_code,
      expires_in: startData.expires_in,
      interval: startData.interval,
    }),
  });

  if (!completeResponse.ok) {
    setStatus(`GitHub authorization failed: ${completeResponse.status}`);
    return;
  }

  setStatus("GitHub account connected in the backend.");
}

document.getElementById("save").addEventListener("click", () => {
  saveSettings().catch((error) => setStatus(error.message));
});

document.getElementById("capture").addEventListener("click", () => {
  captureLeetCodeSession().catch((error) => setStatus(error.message));
});

document.getElementById("connectGithub").addEventListener("click", () => {
  connectGitHub().catch((error) => setStatus(error.message));
});

loadSettings().catch((error) => setStatus(error.message));