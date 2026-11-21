// ---------- Login check ----------
const token = localStorage.getItem("token");
if (!token) {
  window.location.href = "/";
}

function logout() {
  localStorage.removeItem("token");
  window.location.href = "/";
}

// Call the API with the login token. If the token is refused, go back to login.
async function api(path, method) {
  const response = await fetch(path, {
    method: method || "GET",
    headers: { "Authorization": "Bearer " + token }
  });
  if (response.status === 401) {
    logout();
    return null;
  }
  return response.json();
}

// Write a line in the system log panel
function log(text) {
  const box = document.getElementById("log");
  const time = new Date().toLocaleTimeString();
  box.textContent += "[" + time + "] " + text + "\n";
  box.scrollTop = box.scrollHeight;
}

// A MAC is random if the second bit of the first byte is 1
function isRandomMac(mac) {
  return (parseInt(mac.split(":")[0], 16) & 2) !== 0;
}

// ---------- Charts ----------
let donutChart = null;
let lineChart = null;

function drawDonut(real, random) {
  if (donutChart) { donutChart.destroy(); }
  donutChart = new Chart(document.getElementById("donut"), {
    type: "doughnut",
    data: {
      labels: ["Real MAC", "Random MAC"],
      datasets: [{
        data: [real, random],
        backgroundColor: ["#00ff9c", "#ff2e63"],
        borderColor: "#05080a"
      }]
    },
    options: {
      maintainAspectRatio: false,
      plugins: { legend: { labels: { color: "#7dffc8" } } }
    }
  });
}

function drawLine(labels, values) {
  if (lineChart) { lineChart.destroy(); }
  lineChart = new Chart(document.getElementById("line"), {
    type: "line",
    data: {
      labels: labels,
      datasets: [{
        label: "Devices found",
        data: values,
        borderColor: "#00e5ff",
        backgroundColor: "rgba(0, 229, 255, 0.15)",
        fill: true,
        tension: 0.3
      }]
    },
    options: {
      maintainAspectRatio: false,
      scales: {
        x: { ticks: { color: "#7dffc8" }, grid: { color: "#0a3" } },
        y: { beginAtZero: true, ticks: { color: "#7dffc8", precision: 0 }, grid: { color: "#0a3" } }
      },
      plugins: { legend: { labels: { color: "#7dffc8" } } }
    }
  });
}

// ---------- Display the data ----------
function renderDevices(devices) {
  const body = document.getElementById("devicesBody");
  body.innerHTML = "";
  let random = 0;

  for (const device of devices) {
    if (isRandomMac(device.mac)) { random += 1; }
    const row = document.createElement("tr");
    const values = [device.ip, device.mac, device.vendor, device.hostname, device.last_seen];
    for (const value of values) {
      const cell = document.createElement("td");
      // textContent (not innerHTML) so that device names can never run code
      cell.textContent = value;
      row.appendChild(cell);
    }
    body.appendChild(row);
  }

  document.getElementById("statDevices").textContent = devices.length;
  document.getElementById("statRandom").textContent = random;
  drawDonut(devices.length - random, random);
}

function renderScans(scans) {
  if (scans.length > 0) {
    document.getElementById("statLast").textContent = scans[0].created_at;
    document.getElementById("statIp").textContent = scans[0].public_ip || "-";
  }
  // The API gives the newest first, the chart needs the oldest first
  const ordered = scans.slice().reverse();
  const labels = ordered.map(function (scan) { return scan.created_at.slice(11, 19); });
  const values = ordered.map(function (scan) { return scan.device_count; });
  drawLine(labels, values);
}

async function loadAll() {
  const me = await api("/api/me");
  if (me) {
    document.getElementById("userInfo").textContent = "user: " + me.username + " | role: " + me.role;
  }
  const devices = await api("/api/devices");
  if (devices) { renderDevices(devices); }
  const scans = await api("/api/scans");
  if (scans) { renderScans(scans); }
  log("data refreshed");
}

// ---------- Agent token ----------
async function createToken() {
  if (!confirm("This cancels your old agent token. Continue?")) { return; }
  const data = await api("/api/agent/token", "POST");
  if (!data) { return; }
  document.getElementById("tokenValue").textContent = data.agent_token;
  document.getElementById("cmdExample").textContent =
    "python agent.py --token " + data.agent_token + " --server " + window.location.origin;
  document.getElementById("tokenBox").classList.remove("hidden");
  log("new agent token created");
}

document.getElementById("tokenBtn").addEventListener("click", createToken);
document.getElementById("logoutBtn").addEventListener("click", logout);
document.getElementById("copyBtn").addEventListener("click", function () {
  navigator.clipboard.writeText(document.getElementById("tokenValue").textContent);
  log("token copied");
});

// ---------- Start ----------
log("dashboard started");
loadAll();
// Refresh every 10 seconds, so new scans from the agent appear by themselves
setInterval(loadAll, 10000);
