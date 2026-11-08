// ---------- Matrix rain ----------
const canvas = document.getElementById("matrix");
const ctx = canvas.getContext("2d");
const chars = "01ABCDEF<>/{}$#";
const size = 16;
let drops = [];

function init() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  drops = Array(Math.floor(canvas.width / size)).fill(1);
}
init();
window.addEventListener("resize", init);

function draw() {
  ctx.fillStyle = "rgba(0, 0, 0, 0.08)";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#00ff9c";
  ctx.font = size + "px monospace";
  for (let i = 0; i < drops.length; i++) {
    const t = chars[Math.floor(Math.random() * chars.length)];
    ctx.fillText(t, i * size, drops[i] * size);
    if (drops[i] * size > canvas.height && Math.random() > 0.975) {
      drops[i] = 0;
    }
    drops[i]++;
  }
}
setInterval(draw, 50);

// ---------- Typing effect ----------
const lines = [
  "> initializing secure channel...",
  "> scanning network interfaces...",
  "> authentication required"
];
const term = document.getElementById("terminal");
let l = 0, c = 0;

function type() {
  if (l >= lines.length) return;
  if (c < lines[l].length) {
    term.textContent += lines[l][c];
    c++;
    setTimeout(type, 35);
  } else {
    term.textContent += "\n";
    l++;
    c = 0;
    setTimeout(type, 300);
  }
}
type();

// ---------- Login / Register switch ----------
let registerMode = false;
const emailInput = document.getElementById("email");
const btn = document.getElementById("submitBtn");
const switchText = document.getElementById("switchMode");
const msg = document.getElementById("msg");

switchText.addEventListener("click", function () {
  registerMode = !registerMode;
  if (registerMode) {
    emailInput.classList.remove("hidden");
    btn.textContent = "CREATE ACCOUNT";
    switchText.textContent = "[ back to login ]";
  } else {
    emailInput.classList.add("hidden");
    btn.textContent = "ACCESS SYSTEM";
    switchText.textContent = "[ create new account ]";
  }
  msg.textContent = "";
});

