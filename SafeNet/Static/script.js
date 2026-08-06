/* ═══════════════════════════════════════════════════════════════════════════
   SafeNet — script.js
   Theme · Scroll animations · Scan history · Loading · Char counter ·
   Confetti · Toast · Popup · Page transitions
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
    syncSettingsToggle(isDark);
}

// Expose globally so settings.html onclick="setTheme(...)" works
window.setTheme = applyTheme;

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
        toggle.classList.remove("bg-outline");
        toggle.classList.add("bg-primary");
        thumb.classList.remove("translate-x-1");
        thumb.classList.add("translate-x-6");
    } else {
        toggle.classList.remove("bg-primary");
        toggle.classList.add("bg-outline");
        thumb.classList.remove("translate-x-6");
        thumb.classList.add("translate-x-1");
    }

    document.querySelectorAll(".theme-option").forEach(btn => {
        const active = btn.dataset.theme === (isDark ? "dark" : "light");
        btn.classList.toggle("border-primary", active);
        btn.classList.toggle("border-outline-variant", !active);
    });
}

// ─── Init on every page load (before DOMContentLoaded) ───────────────────────

(function initTheme() {
    const isDark = document.documentElement.classList.contains("dark");
    updateThemeIcons(isDark);
    syncSettingsToggle(isDark);
})();


// ═══════════════════════════════════════════════════════════════════════════
//  INTERSECTION OBSERVER — scroll-triggered reveals
// ═══════════════════════════════════════════════════════════════════════════

function initRevealObserver() {
    const selectors = [
        '.reveal',
        '.reveal-left',
        '.reveal-right',
        '.reveal-pop',
        '.reveal-stagger',
    ];

    const targets = document.querySelectorAll(selectors.join(','));
    if (!targets.length) return;

    // Anything already in viewport on load fires immediately
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target); // fire once
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -40px 0px',
    });

    targets.forEach(el => observer.observe(el));
}


// ═══════════════════════════════════════════════════════════════════════════
//  PAGE TRANSITIONS
// ═══════════════════════════════════════════════════════════════════════════

function initPageTransitions() {
    // Add page-content class to main content wrapper for entrance animation
    const main = document.querySelector('main');
    if (main) main.classList.add('page-content');

    // Fade-out on internal link clicks
    document.querySelectorAll('a[href]').forEach(link => {
        const href = link.getAttribute('href');
        if (!href || href.startsWith('#') || href.startsWith('http') ||
            href.startsWith('mailto') || link.getAttribute('target') === '_blank') return;

        link.addEventListener('click', function (e) {
            e.preventDefault();
            document.body.classList.add('page-leaving');
            setTimeout(() => { window.location.href = href; }, 180);
        });
    });
}


// ═══════════════════════════════════════════════════════════════════════════
//  STAT COUNTER ANIMATION  (counts up from 0 to target value)
// ═══════════════════════════════════════════════════════════════════════════

function animateCounter(el) {
    const raw    = el.dataset.target || el.textContent.trim();
    const suffix = raw.replace(/[\d,]/g, '').trim();   // e.g. '+', 'M+'
    const target = parseInt(raw.replace(/[^0-9]/g, ''), 10);
    if (isNaN(target)) return;

    const duration = 1200;
    const start    = performance.now();
    el.textContent = '0' + suffix;

    function step(now) {
        const elapsed  = now - start;
        const progress = Math.min(elapsed / duration, 1);
        // easeOutExpo
        const eased = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
        const value = Math.floor(eased * target);
        el.textContent = value.toLocaleString() + suffix;
        if (progress < 1) requestAnimationFrame(step);
    }

    requestAnimationFrame(step);
}

function initCounterAnimations() {
    const counters = document.querySelectorAll('[data-counter]');
    if (!counters.length) return;

    const obs = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                obs.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });

    counters.forEach(el => obs.observe(el));
}


// ═══════════════════════════════════════════════════════════════════════════
//  SAFETY SCORE RING  — animate stroke-dashoffset on enter
// ═══════════════════════════════════════════════════════════════════════════

function initScoreRings() {
    document.querySelectorAll('[data-ring-target]').forEach(circle => {
        const target = parseInt(circle.dataset.ringTarget, 10);
        const total  = parseFloat(circle.dataset.ringTotal || '283');

        // Start at empty (full dashoffset = total circumference)
        circle.style.strokeDashoffset = total;

        const obs = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    // Small delay so the transition is visible
                    setTimeout(() => {
                        circle.style.strokeDashoffset = total - (target / 100 * total);
                    }, 150);
                    obs.unobserve(entry.target);
                }
            });
        }, { threshold: 0.3 });

        obs.observe(circle);
    });
}


// ═══════════════════════════════════════════════════════════════════════════
//  TOAST NOTIFICATIONS
// ═══════════════════════════════════════════════════════════════════════════

function showToast(message, type = 'info', duration = 3500) {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText =
            'position:fixed;bottom:1.5rem;right:1.5rem;z-index:9999;display:flex;flex-direction:column;gap:0.5rem;pointer-events:none;';
        document.body.appendChild(container);
    }

    const colours = {
        success: 'bg-secondary-container text-on-secondary-container border-secondary/30',
        error:   'bg-error-container text-on-error-container border-error/30',
        warning: 'bg-tertiary-container text-on-tertiary border-tertiary/30',
        info:    'bg-primary-container text-on-primary-container border-primary/30',
    };

    const icons = {
        success: 'check_circle',
        error:   'error',
        warning: 'warning_amber',
        info:    'info',
    };

    const toast = document.createElement('div');
    toast.className =
        `toast pointer-events-auto flex items-center gap-2.5 px-4 py-3 rounded-xl border shadow-lg text-sm font-medium max-w-xs ${colours[type] || colours.info}`;
    toast.innerHTML =
        `<span class="material-symbols-outlined fill-icon text-base">${icons[type] || 'info'}</span>
         <span>${escHtml(message)}</span>`;

    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('hiding');
        toast.addEventListener('animationend', () => toast.remove(), { once: true });
    }, duration);
}

// Expose globally for inline use
window.showToast = showToast;


// ═══════════════════════════════════════════════════════════════════════════
//  POPUP / MODAL
// ═══════════════════════════════════════════════════════════════════════════

function openPopup(id) {
    const overlay = document.getElementById(id);
    if (!overlay) return;
    overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
    // Trap focus
    const firstFocusable = overlay.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
    if (firstFocusable) firstFocusable.focus();
}

function closePopup(id) {
    const overlay = document.getElementById(id);
    if (!overlay) return;
    overlay.classList.remove('open');
    document.body.style.overflow = '';
}

// Close popup on overlay click
document.addEventListener('click', function (e) {
    if (e.target.classList.contains('popup-overlay')) {
        e.target.classList.remove('open');
        document.body.style.overflow = '';
    }
});

// Close on Escape
document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
        document.querySelectorAll('.popup-overlay.open').forEach(el => {
            el.classList.remove('open');
            document.body.style.overflow = '';
        });
    }
});

window.openPopup  = openPopup;
window.closePopup = closePopup;


// ═══════════════════════════════════════════════════════════════════════════
//  CONFETTI  (used on report_success page)
// ═══════════════════════════════════════════════════════════════════════════

function launchConfetti() {
    const colours = ['#0058be', '#006c49', '#924700', '#ba1a1a', '#adc6ff', '#6cf8bb', '#ffdcc6'];
    const count   = 80;

    for (let i = 0; i < count; i++) {
        const piece = document.createElement('div');
        piece.className = 'confetti-piece';

        const colour = colours[Math.floor(Math.random() * colours.length)];
        const left   = Math.random() * 100;
        const delay  = Math.random() * 1.2;
        const dur    = 2.0 + Math.random() * 1.5;
        const size   = 6 + Math.random() * 8;
        const shape  = Math.random() > 0.5 ? '50%' : '2px';

        piece.style.cssText =
            `left:${left}vw;
             width:${size}px;
             height:${size}px;
             background:${colour};
             border-radius:${shape};
             animation-duration:${dur}s;
             animation-delay:${delay}s;`;

        document.body.appendChild(piece);
        piece.addEventListener('animationend', () => piece.remove(), { once: true });
    }
}

window.launchConfetti = launchConfetti;


// ═══════════════════════════════════════════════════════════════════════════
//  DOM READY
// ═══════════════════════════════════════════════════════════════════════════

document.addEventListener("DOMContentLoaded", function () {

    // ── Core init ─────────────────────────────────────────────────────────
    initRevealObserver();
    initCounterAnimations();
    initScoreRings();
    initPageTransitions();

    // ── Scan button loading state ──────────────────────────────────────────
    document.querySelectorAll("form[action*='scanner']").forEach(function (form) {
        form.addEventListener("submit", function () {
            const btn = form.querySelector("button[type='submit']");
            if (!btn) return;
            const url = form.querySelector("input[name='url']")?.value?.trim();
            if (!url) return;
            btn.disabled = true;
            btn.innerHTML =
                '<span class="spinner"></span>&nbsp;<span>Scanning&hellip;</span>';
            btn.classList.add('scan-ring');
            saveScanHistory(url);
        });
    });

    // ── Pre-fill URL from ?url= query param ────────────────────────────────
    const preUrl = new URLSearchParams(window.location.search).get("url");
    if (preUrl) {
        const urlInput = document.querySelector("input[name='url']");
        if (urlInput && !urlInput.value) urlInput.value = preUrl;
    }

    // ── Render scan history in sidebar ────────────────────────────────────
    renderScanHistory();

    // ── Report form char counter ──────────────────────────────────────────
    const desc    = document.getElementById("description");
    const counter = document.getElementById("char-count");
    if (desc && counter) {
        counter.textContent = desc.value.length;
        desc.addEventListener("input", function () {
            const len = desc.value.length;
            counter.textContent = len;
            counter.classList.toggle("text-error", len > 450);
        });
    }

    // ── Smooth scroll for in-page anchor links ────────────────────────────
    document.querySelectorAll("a[href^='#']").forEach(anchor => {
        anchor.addEventListener("click", function (e) {
            const target = document.querySelector(this.getAttribute("href"));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: "smooth", block: "start" });
            }
        });
    });

    // ── Stagger report list items ─────────────────────────────────────────
    // Reports page: add reveal + delay to each list card
    const reportCards = document.querySelectorAll('.report-card');
    reportCards.forEach((card, i) => {
        card.style.transitionDelay = `${i * 0.05}s`;
        card.classList.add('reveal');
    });
    // Trigger observer now that classes are added
    initRevealObserver();

    // ── Confetti auto-launch on success page ──────────────────────────────
    if (document.getElementById('confetti-trigger')) {
        setTimeout(launchConfetti, 400);
    }

    // ── Score ring in dashboard ────────────────────────────────────────────
    const dashRing = document.getElementById('dashboard-score-ring');
    if (dashRing) {
        // Already handled by initScoreRings via data-ring-target
    }

    // ── Tab/pill active state for education topic pills ───────────────────
    const topicPills = document.querySelectorAll('.topic-pill-btn');
    topicPills.forEach(pill => {
        pill.addEventListener('click', () => {
            topicPills.forEach(p => p.classList.remove('ring-2', 'ring-primary'));
            pill.classList.add('ring-2', 'ring-primary');
        });
    });

    // ── Input field micro-interactions ────────────────────────────────────
    document.querySelectorAll('input[required], textarea[required]').forEach(field => {
        field.addEventListener('blur', function () {
            const parent = this.closest('.field-wrapper') || this.parentElement;
            if (this.validity.valid && this.value.trim()) {
                parent.classList.add('field-success');
            } else {
                parent.classList.remove('field-success');
            }
        });

        field.addEventListener('input', function () {
            const parent = this.closest('.field-wrapper') || this.parentElement;
            if (this.validity.valid && this.value.trim()) {
                parent.classList.add('field-success');
            } else {
                parent.classList.remove('field-success');
            }
        });
    });

});


// ═══════════════════════════════════════════════════════════════════════════
//  SCAN HISTORY  (localStorage)
// ═══════════════════════════════════════════════════════════════════════════

const HISTORY_KEY = "safenet_scan_history";
const MAX_HISTORY = 8;

function saveScanHistory(url) {
    try {
        let history = JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
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
    showToast('Scan history cleared.', 'info', 2500);
}

function renderScanHistory() {
    const container = document.getElementById("scan-history-list");
    if (!container) return;
    const history = getScanHistory();
    if (history.length === 0) {
        container.innerHTML =
            '<p class="text-xs text-on-surface-variant italic px-1 py-1">No recent scans.</p>';
        return;
    }
    container.innerHTML = history.map(item => {
        const short = item.url.replace(/^https?:\/\//, "").slice(0, 36);
        const date  = new Date(item.ts).toLocaleDateString("en-NZ", {
            day: "numeric", month: "short",
        });
        return `<button onclick="reScan('${escHtml(item.url)}')"
                        class="w-full text-left flex items-center gap-2 px-2 py-1.5 rounded-lg
                               hover:bg-surface-container-high transition-colors group text-xs">
                    <span class="material-symbols-outlined text-outline text-[15px] group-hover:text-primary flex-shrink-0">history</span>
                    <span class="flex-1 truncate text-on-surface-variant group-hover:text-on-surface font-mono">${escHtml(short)}</span>
                    <span class="text-outline text-[10px] whitespace-nowrap flex-shrink-0">${date}</span>
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


// ═══════════════════════════════════════════════════════════════════════════
//  UTILITIES
// ═══════════════════════════════════════════════════════════════════════════

function escHtml(str) {
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}
