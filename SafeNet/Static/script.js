/* ═══════════════════════════════════════════════════════════════════════════
   SafeNet — script.js
   Theme toggle · Scan history · Loading states · Char counter · Scroll
   ═══════════════════════════════════════════════════════════════════════════ */

// ─── Theme ────────────────────────────────────────────────────────────────────

function toggleTheme() {
    const isDark = document.documentElement.classList.contains("dark");
    applyTheme(isDark ? "light" : "dark");
}

function applyTheme(theme) {
    const isDark = theme === "dark";
    document.documentElement.classList.toggle("dark", isDark);
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
    updateThemeIcons(isDark);
    // Sync settings page toggle if present
    syncSettingsToggle(isDark);
}

function updateThemeIcons(isDark) {
    const desktopIcon  = document.getElementById("desktop-theme-icon");
    const desktopLabel = document.getElementById("desktop-theme-label");
    const mobileIcon   = document.getElementById("mobile-theme-icon");
    if (desktopIcon)  desktopIcon.textContent  = isDark ? "light_mode" : "dark_mode";
    if (desktopLabel) desktopLabel.textContent = isDark ? "Light Mode" : "Dark Mode";
    if (mobileIcon)   mobileIcon.textContent   = isDark ? "light_mode" : "dark_mode";
}

function syncSettingsToggle(isDark) {
    const toggle = document.getElementById("settings-theme-toggle");
    const thumb  = document.getElementById("settings-thumb");
    if (!toggle || !thumb) return;
    toggle.setAttribute("aria-checked", String(isDark));
    if (isDark) {
        toggle.classList.replace("bg-outline", "bg-primary");
        thumb.classList.replace("translate-x-1", "translate-x-6");
    } else {
        toggle.classList.replace("bg-primary", "bg-outline");
        thumb.classList.replace("translate-x-6", "translate-x-1");
    }
    // Highlight correct theme card
    document.querySelectorAll(".theme-option").forEach(btn => {
        const active = btn.dataset.theme === (isDark ? "dark" : "light");
        btn.classList.toggle("border-primary", active);
        btn.classList.toggle("border-outline-variant", !active);
    });
}

// ─── Initialise on every page load ───────────────────────────────────────────

(function init() {
    const isDark = document.documentElement.classList.contains("dark");
    updateThemeIcons(isDark);
    syncSettingsToggle(isDark);
})();


// ─── Scan form: loading state + history ──────────────────────────────────────

document.addEventListener("DOMContentLoaded", function () {

    // ── Scan button loading state ─────────────────────────────────────────
    const scanForm = document.querySelector("form[action*='scanner']");
    if (scanForm) {
        scanForm.addEventListener("submit", function () {
            const btn = scanForm.querySelector("button[type='submit']");
            if (!btn) return;
            const url = scanForm.querySelector("input[name='url']")?.value?.trim();
            if (!url) return; // let HTML validation handle it
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner"></span> Scanning...';
            // Save to scan history
            saveScanHistory(url);
        });
        // Populate URL from query param if redirected with ?url=
        const params = new URLSearchParams(window.location.search);
        const preUrl = params.get("url");
        if (preUrl) {
            const urlInput = scanForm.querySelector("input[name='url']");
            if (urlInput && !urlInput.value) urlInput.value = preUrl;
        }
    }

    // ── Scan history sidebar ──────────────────────────────────────────────
    renderScanHistory();

    // ── Report form char counter ──────────────────────────────────────────
    const desc    = document.getElementById("description");
    const counter = document.getElementById("char-count");
    if (desc && counter) {
        counter.textContent = desc.value.length;
        desc.addEventListener("input", function () {
            const len = desc.value.length;
            counter.textContent = len;
            counter.classList.toggle("text-red-600", len > 450);
        });
    }

    // ── Result card entrance animation ───────────────────────────────────
    const resultCards = document.querySelectorAll(".result-enter");
    resultCards.forEach(card => card.classList.add("result-enter"));

    // ── Smooth scroll for hash links ──────────────────────────────────────
    document.querySelectorAll("a[href^='#']").forEach(anchor => {
        anchor.addEventListener("click", function (e) {
            const target = document.querySelector(this.getAttribute("href"));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: "smooth", block: "start" });
            }
        });
    });

    // ── Auto-dismiss flash messages ───────────────────────────────────────
    const flash = document.getElementById("flash-message");
    if (flash) {
        setTimeout(() => {
            flash.style.transition = "opacity 0.5s ease";
            flash.style.opacity = "0";
            setTimeout(() => flash.remove(), 500);
        }, 4000);
    }

});


// ─── Scan history (localStorage) ─────────────────────────────────────────────

const HISTORY_KEY = "safenet_scan_history";
const MAX_HISTORY = 8;

function saveScanHistory(url) {
    try {
        let history = JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
        // Remove duplicate if exists
        history = history.filter(item => item.url !== url);
        history.unshift({ url, ts: new Date().toISOString() });
        if (history.length > MAX_HISTORY) history = history.slice(0, MAX_HISTORY);
        localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    } catch (e) { /* storage unavailable */ }
}

function getScanHistory() {
    try {
        return JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
    } catch (e) { return []; }
}

function clearScanHistory() {
    localStorage.removeItem(HISTORY_KEY);
    renderScanHistory();
}

function renderScanHistory() {
    const container = document.getElementById("scan-history-list");
    if (!container) return;
    const history = getScanHistory();
    if (history.length === 0) {
        container.innerHTML = '<p class="text-xs text-on-surface-variant italic px-1">No recent scans.</p>';
        return;
    }
    container.innerHTML = history.map(item => {
        const short = item.url.replace(/^https?:\/\//, "").slice(0, 36);
        const date  = new Date(item.ts).toLocaleDateString("en-NZ", { day: "numeric", month: "short" });
        return `<button onclick="reScan('${escapeHtml(item.url)}')"
                        class="w-full text-left flex items-center gap-2 px-2 py-1.5 rounded-lg
                               hover:bg-surface-container-high transition-colors group text-xs">
                    <span class="material-symbols-outlined text-outline text-[16px] group-hover:text-primary">history</span>
                    <span class="flex-1 truncate text-on-surface-variant group-hover:text-on-surface">${escapeHtml(short)}</span>
                    <span class="text-outline text-[10px] whitespace-nowrap">${date}</span>
                </button>`;
    }).join("");
}

function reScan(url) {
    const input = document.querySelector("input[name='url']");
    if (input) {
        input.value = url;
        input.closest("form")?.requestSubmit();
    }
}

function escapeHtml(str) {
    return str.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}


// ─── Settings page helpers ────────────────────────────────────────────────────

// Exposed globally so settings.html onclick can call it
window.setTheme = applyTheme;
