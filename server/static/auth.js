document.getElementById("submitBtn").addEventListener("click", async function () {
  const message = document.getElementById("msg");
  const username = document.getElementById("username").value.trim();
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const isRegister = !document.getElementById("email").classList.contains("hidden");

  message.style.color = "#ff2e63";
  message.textContent = "";

  let url = "/api/login";
  let body = { username: username, password: password };
  if (isRegister) {
    url = "/api/register";
    body = { username: username, email: email, password: password };
  }

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    const data = await response.json();

    if (!response.ok) {
      if (typeof data.detail === "string") {
        message.textContent = data.detail;
      } else {
        message.textContent = "Invalid data: username 3+ chars, password 8+ chars";
      }
      return;
    }

    if (isRegister) {
      document.getElementById("switchMode").click();
      message.style.color = "#00ff9c";
      message.textContent = "Account created. You can login now.";
    } else {
      localStorage.setItem("token", data.access_token);
      window.location.href = "/dashboard";
    }
  } catch (error) {
    message.textContent = "Server not reachable";
  }
});