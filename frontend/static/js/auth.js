document.getElementById("loginForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const loginValue = document.getElementById("login").value;
    const password = document.getElementById("password").value;
    const errorMsg = document.getElementById("errorMsg");
    try {
        const data = await login(loginValue, password);
        localStorage.setItem("token", data.access_token);
        window.location.href = "/static/pages/index.html";
    } catch (err) {
        errorMsg.textContent = err.message;
    }
});

const token = localStorage.getItem("token");
if (token && window.location.pathname.includes("login")) {
    window.location.href = "/static/pages/index.html";
}
