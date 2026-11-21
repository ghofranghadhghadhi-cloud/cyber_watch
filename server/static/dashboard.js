// If there is no login token, go back to the login page
const token = localStorage.getItem("token");
if (!token) {
  window.location.href = "/";
}

// ---------- Helpers ----------
// fetch with the login token; if the token is bad, go back to the login page
function authFetch(url, options) {
  options = options || {};
  options.headers = Object.assign({ Authorization: "Bearer " + token }, options.headers || {});
  return fetch(url, options).then(function (response) {
    if (response.status === 401) {
      localStorage.removeItem("token");
      window.location.href = "/";
      throw new Error("unauthorized");
    }
    return response;
  });
}

// The database stores UTC time like "2026-11-21 10:30:00"
function parseTime(text) {
  return new Date(text.replace(" ", "T") + "Z");
}

function timeAgo(date) {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
  if (seconds < 60) {
    return seconds + " s ago";
  }
  if (seconds < 3600) {
    return Math.floor(seconds / 60) + " min ago";
  }
  if (seconds < 86400) {
    return Math.floor(seconds / 3600) + " h ago";
  }
  return Math.floor(seconds / 86400) + " d ago";
}

function setText(id, text) {
  document.getElementById(id).textContent = text;
}

// ---------- Cards ----------
function renderCards(devices, scans) {
  setText("cardDevices", String(devices.length));

  const agent = document.getElementById("cardAgent");
  if (scans.length === 0) {
    setText("cardLastScan", "never");
    setText("cardPublicIp", "-");
    agent.textContent = "OFFLINE";
    agent.className = "value offline";
    return;
  }

  const last = scans[0]; // the API returns the newest scan first
  const lastDate = parseTime(last.created_at);
  setText("cardLastScan", timeAgo(lastDate));
  setText("cardPublicIp", last.public_ip || "-");

  // The agent is "online" if it sent a scan in the last 5 minutes
  const online = Date.now() - lastDate.getTime() < 5 * 60 * 1000;
  agent.textContent = online ? "ONLINE" : "OFFLINE";
  agent.className = online ? "value online" : "value offline";
}

// ---------- Load data ----------
function loadData() {
  Promise.all([
    authFetch("/api/devices").then(function (r) {
      return r.json();
    }),
    authFetch("/api/scans").then(function (r) {
      return r.json();
    }),
  ])
    .then(function (results) {
      renderCards(results[0], results[1]);
    })
    .catch(function () {});
}

authFetch("/api/me")
  .then(function (r) {
    return r.json();
  })
  .then(function (user) {
    setText("userInfo", "> " + user.username + " | role: " + user.role);
    loadData();
    setInterval(loadData, 10000); // refresh every 10 seconds
  })
  .catch(function () {});

// ---------- Logout ----------
document.getElementById("logoutBtn").addEventListener("click", function () {
  localStorage.removeItem("token");
  window.location.href = "/";
});
