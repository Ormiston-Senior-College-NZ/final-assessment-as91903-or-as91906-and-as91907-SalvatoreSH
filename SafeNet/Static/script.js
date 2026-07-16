function applyTheme(theme) {
    const isDark = theme === "dark";
    document.body.classList.toggle("dark", isDark);
    document.documentElement.setAttribute("data-theme", theme);

    const toggleButton = document.querySelector(".theme-toggle");
    if (toggleButton) {
        toggleButton.textContent = isDark ? "☀️ Light Mode" : "🌙 Dark Mode";
        toggleButton.setAttribute("aria-pressed", isDark ? "true" : "false");
    }
}

function toggleTheme() {
    const nextTheme = document.body.classList.contains("dark") ? "light" : "dark";
    localStorage.setItem("theme", nextTheme);
    applyTheme(nextTheme);
}

document.addEventListener("DOMContentLoaded", function () {
    const storedTheme = localStorage.getItem("theme");
    const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    const theme = storedTheme || (prefersDark ? "dark" : "light");
    applyTheme(theme);
});

window.toggleTheme = toggleTheme;