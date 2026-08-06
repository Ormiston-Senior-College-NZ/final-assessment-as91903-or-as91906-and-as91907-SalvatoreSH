import os
import json
import re
from datetime import datetime
from urllib.parse import urlparse, quote_plus
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__, static_folder="Static", template_folder="templates")

# Register urlencode as a Jinja2 filter so templates can use {{ value | urlencode }}
# quote_plus correctly encodes a plain string value for use in a query parameter.
app.jinja_env.filters["urlencode"] = lambda s: quote_plus(str(s))

REPORTS_FILE = os.path.join(os.path.dirname(__file__), "reports.json")

# ─── Daily tips (rotates by day of year) ─────────────────────────────────────

TIPS = [
    "Use unique, complex passwords for every account and consider a password manager.",
    "Always check a URL before clicking — hover over links to see the real destination.",
    "Enable two-factor authentication on your email, banking, and social media accounts.",
    "Never enter personal details on a site you reached by clicking an email link.",
    "Shortened URLs (bit.ly, tinyurl) hide the true destination — scan them first.",
    "Legitimate banks and government agencies will never ask for your password by email.",
    "Keep your operating system and apps updated — updates patch security vulnerabilities.",
    "Back up important files regularly so ransomware can't permanently lock you out.",
    "Be sceptical of 'you've won' messages — if it sounds too good to be true, it is.",
    "Check the sender's full email address carefully, not just the display name.",
    "Public Wi-Fi is not secure — avoid banking or shopping on public networks.",
    "Report scams to CERT NZ (cert.govt.nz) to help protect other New Zealanders.",
    "A padlock icon in the browser bar means the connection is encrypted, not that the site is safe.",
    "If you're unsure about a call from a company, hang up and call them back on their official number.",
]

def get_daily_tip():
    idx = datetime.now().timetuple().tm_yday % len(TIPS)
    return TIPS[idx]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def load_reports():
    if not os.path.exists(REPORTS_FILE):
        with open(REPORTS_FILE, "w") as f:
            json.dump([], f)
    with open(REPORTS_FILE, "r") as f:
        try:
            return json.load(f)
        except (json.JSONDecodeError, ValueError):
            return []


def save_reports(reports):
    with open(REPORTS_FILE, "w") as f:
        json.dump(reports, f, indent=4)


def analyse_url(url):
    """
    Heuristic URL scanner.
    Returns: { level: 'safe'|'warning'|'danger'|'error', score: int, reasons: [str], title: str }
    """
    reasons = []
    score   = 0
    url_lower = url.lower()

    # ── Protocol ──────────────────────────────────────────────────────────
    if url_lower.startswith("http://"):
        reasons.append("Uses unencrypted HTTP — the connection is not secure.")
        score += 20

    # ── Suspicious TLDs ───────────────────────────────────────────────────
    BAD_TLDS = [
        ".tk", ".ml", ".ga", ".cf", ".gq", ".xyz", ".top", ".click",
        ".loan", ".work", ".zip", ".ru", ".su", ".pw", ".cc", ".biz"
    ]
    for tld in BAD_TLDS:
        if tld in url_lower:
            reasons.append(f"Uses a high-risk domain extension ({tld}) commonly associated with scam sites.")
            score += 25
            break

    # ── IP address as domain ───────────────────────────────────────────────
    if re.match(r"https?://(\d{1,3}\.){3}\d{1,3}", url):
        reasons.append("Uses a raw IP address as the domain — a common phishing technique.")
        score += 35

    # ── Subdomain spoofing ─────────────────────────────────────────────────
    TRUSTED_BRANDS = [
        "paypal", "anz", "bnz", "westpac", "kiwibank", "asb", "nzpost",
        "google", "microsoft", "apple", "amazon", "facebook", "instagram",
        "netflix", "discord", "steam", "myir", "ird", "govt", "acc",
        "inland-revenue", "nzta", "msd", "servicenow",
    ]
    try:
        parsed   = urlparse(url)
        hostname = parsed.hostname or ""
        parts    = hostname.split(".")
        if len(parts) >= 3:
            subdomain = ".".join(parts[:-2]).lower()
            for brand in TRUSTED_BRANDS:
                if brand in subdomain:
                    reasons.append(
                        f"Subdomain spoofing — '{brand}' appears as a subdomain of an unrelated domain. "
                        f"Attackers use this to mimic trusted organisations."
                    )
                    score += 40
                    break
    except Exception:
        pass

    # ── Suspicious keywords ────────────────────────────────────────────────
    BAD_KEYWORDS = [
        "login", "verify", "secure", "update", "confirm", "account",
        "banking", "password", "credential", "signin", "free-prize",
        "win-prize", "claim-now", "urgent", "suspended", "unusual-activity",
        "alert", "locked", "reactivate",
    ]
    matched_kw = [kw for kw in BAD_KEYWORDS if kw in url_lower]
    if len(matched_kw) >= 2:
        reasons.append(
            f"Multiple suspicious keywords detected in the URL: {', '.join(matched_kw[:4])}."
        )
        score += 20
    elif len(matched_kw) == 1:
        reasons.append(f"Suspicious keyword detected in the URL: '{matched_kw[0]}'.")
        score += 10

    # ── URL shorteners ─────────────────────────────────────────────────────
    SHORTENERS = ["bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly",
                  "short.link", "rb.gy", "cutt.ly", "is.gd"]
    for s in SHORTENERS:
        if s in url_lower:
            reasons.append(
                "Shortened URL — the true destination is hidden. "
                "Shortened links are frequently used to disguise malicious sites."
            )
            score += 15
            break

    # ── Excessive subdomains ───────────────────────────────────────────────
    try:
        parts = urlparse(url).hostname.split(".")
        if len(parts) > 4:
            reasons.append(
                "Unusually deep subdomain chain — attackers use this to bury the real domain "
                "and make a URL appear legitimate."
            )
            score += 15
    except Exception:
        pass

    # ── Very long URL ──────────────────────────────────────────────────────
    if len(url) > 150:
        reasons.append("URL is unusually long — sometimes used to obscure the true destination.")
        score += 10

    # ── Clamp and level ────────────────────────────────────────────────────
    score = min(score, 100)

    if score >= 60:
        return {
            "level":   "danger",
            "score":   score,
            "title":   "Dangerous — do not visit this site.",
            "reasons": reasons or ["This URL matches multiple high-risk patterns."],
        }
    elif score >= 25:
        return {
            "level":   "warning",
            "score":   score,
            "title":   "Suspicious — proceed with extreme caution.",
            "reasons": reasons or ["This URL has characteristics associated with suspicious sites."],
        }
    else:
        return {
            "level":   "safe",
            "score":   score,
            "title":   "No threats detected.",
            "reasons": reasons or ["This URL passed all safety checks."],
        }


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    return render_template("landing.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        if email and password:
            return redirect(url_for("dashboard"))
        error = "Please enter both an email address and a password."
    return render_template("login.html", error=error)


@app.route("/dashboard")
def dashboard():
    reports = load_reports()
    recent  = sorted(
        [r for r in reports if r.get("threat_type")],  # skip legacy/blank entries
        key=lambda r: r.get("timestamp", ""),
        reverse=True
    )[:4]
    return render_template(
        "index.html",
        recent_reports=recent,
        total_reports=len(reports),
        tip=get_daily_tip(),
    )


@app.route("/scanner", methods=["GET", "POST"])
def scanner():
    result      = None
    scanned_url = None

    if request.method == "POST":
        url = request.form.get("url", "").strip()

        if not url:
            result = {
                "level": "error",
                "title": "Please enter a URL to scan.",
                "reasons": ["The input field was empty. Enter a full URL starting with http:// or https://"],
                "score": 0,
            }
        elif not url.startswith(("http://", "https://")):
            result = {
                "level": "error",
                "title": "Invalid URL format.",
                "reasons": ["Please enter a URL beginning with http:// or https://  —  e.g. https://example.com"],
                "score": 0,
            }
        else:
            try:
                result      = analyse_url(url)
                scanned_url = url
            except Exception as e:
                result = {
                    "level": "error",
                    "title": "Something went wrong analysing that URL.",
                    "reasons": ["The URL could not be analysed. Please check the format and try again."],
                    "score": 0,
                }

    return render_template("scanner.html", result=result, scanned_url=scanned_url)


@app.route("/report", methods=["GET", "POST"])
def report():
    error         = None
    form_values   = {}

    if request.method == "POST":
        threat_type = request.form.get("threat_type", "").strip()
        url_content = request.form.get("url_content",  "").strip()
        description = request.form.get("description",  "").strip()

        # Preserve form values on error
        form_values = {
            "threat_type": threat_type,
            "url_content": url_content,
            "description": description,
        }

        if not threat_type:
            error = "Please select a threat type."
        elif not url_content:
            error = "Please enter the suspicious URL or message content."
        elif len(description) < 20:
            error = "Please describe the threat in at least 20 characters."
        elif len(description) > 500:
            error = "Description must be 500 characters or fewer."
        else:
            reports = load_reports()
            new_report = {
                "threat_type": threat_type,
                "url_content": url_content,
                "description": description,
                "timestamp":   datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
            reports.append(new_report)
            save_reports(reports)
            return redirect(url_for("report_success"))

    # Pre-fill URL from query string if coming from scanner
    if not form_values.get("url_content"):
        form_values["url_content"] = request.args.get("url", "")

    return render_template("report.html", error=error, form=form_values)


@app.route("/report/success")
def report_success():
    return render_template("report_success.html")


@app.route("/reports")
def reports():
    all_reports = load_reports()
    # Filter out legacy entries that have no threat_type (old schema)
    valid = [r for r in all_reports if r.get("threat_type") or r.get("url_content")]
    valid = sorted(valid, key=lambda r: r.get("timestamp", ""), reverse=True)
    return render_template("reports.html", reports=valid)


@app.route("/education")
def education():
    return render_template("education.html")


@app.route("/settings")
def settings():
    return render_template("settings.html")


# ─── Error handlers ───────────────────────────────────────────────────────────

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("404.html", code=500), 500


if __name__ == "__main__":
    app.run(debug=True)
