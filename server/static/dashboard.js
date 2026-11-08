const token = localStorage.getItem("token");
const box = document.getElementById("terminal");

if (!token) {
  window.location.href = "/";
} else {
  fetch("/api/me", { headers: { "Authorization": "Bearer " + token } })
    .then(function (r) {
      if (!r.ok) { throw new Error("bad token"); }
      return r.json();
    })
    .then(function (d) {
      box.textContent = "> access granted\n> user: " + d.username + "\n> role: " + d.role;
    })
    .catch(function () {
      localStorage.removeItem("token");
      window.location.href = "/";
    });
}

document.getElementById("logoutBtn").addEventListener("click", function () {
  localStorage.removeItem("token");
  window.location.href = "/";
});