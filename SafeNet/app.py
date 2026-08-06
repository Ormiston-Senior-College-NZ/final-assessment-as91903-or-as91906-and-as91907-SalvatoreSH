import os
import json
import re
import uuid
from datetime import datetime
from urllib.parse import urlparse, quote_plus
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__, static_folder="Static", template_folder="templates")

# Secret key for sessions — in production use a real random secret
app.secret_key = os.environ.get("SAFENET_SECRET", "safenet-dev-secret-change-in-prod")

# Register urlencode as a Jinja2 filter
app.jinja_env.filters["urlencode"] = lambda s: quote_plus(str(s))

REPORTS_FILE = os.path.join(os.path.dirname(__file__), "reports.json")
USERS_FILE   = os.path.join(os.path.dirname(__file__), "users.json")


# ─── Password hashing (werkzeug ships with Flask) ─────────────────────────────

from werkzeug.security import generate_password_hash, check_password_hash


# ─── User store helpers ───────────────────────────────────────────────────────

def load_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump([], f)
    with open(USERS_FILE, "r") as f:
        try:
            return json.load(f)
        except (json.JSONDecodeError, ValueError):
            return []


def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)


def find_user_by_email(email):
    return next((u for u in load_users() if u["email"].lower() == email.lower()), None)


def find_user_by_id(uid):
    return next((u for u in load_users() if u["id"] == uid), None)


def current_user():
    """Return the logged-in user dict, or None."""
    uid = session.get("user_id")
    if not uid:
        return None
    return find_user_by_id(uid)


# Make current_user available in every template automatically
@app.context_processor
def inject_user():
    return {"current_user": current_user()}


# ─── Daily tips ───────────────────────────────────────────────────────────────

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


# ─── Report store helpers ─────────────────────────────────────────────────────

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


# ─── URL analyser ─────────────────────────────────────────────────────────────

def analyse_url(url):
    """
    Heuristic URL scanner.
    Returns: { level: 'safe'|'warning'|'danger'|'error', score: int, reasons: [str], title: str }
    """
    reasons   = []
    score     = 0
    url_lower = url.lower()

    if url_lower.startswith("http://"):
        reasons.append("Uses unencrypted HTTP — the connection is not secure.")
        score += 20

    BAD_TLDS = [
        ".tk", ".ml", ".ga", ".cf", ".gq", ".xyz", ".top", ".click",
        ".loan", ".work", ".zip", ".ru", ".su", ".pw", ".cc", ".biz"
    ]
    for tld in BAD_TLDS:
        if tld in url_lower:
            reasons.append(f"Uses a high-risk domain extension ({tld}) commonly associated with scam sites.")
            score += 25
            break

    if re.match(r"https?://(\d{1,3}\.){3}\d{1,3}", url):
        reasons.append("Uses a raw IP address as the domain — a common phishing technique.")
        score += 35

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

    BAD_KEYWORDS = [
        "login", "verify", "secure", "update", "confirm", "account",
        "banking", "password", "credential", "signin", "free-prize",
        "win-prize", "claim-now", "urgent", "suspended", "unusual-activity",
        "alert", "locked", "reactivate",
    ]
    matched_kw = [kw for kw in BAD_KEYWORDS if kw in url_lower]
    if len(matched_kw) >= 2:
        reasons.append(f"Multiple suspicious keywords detected in the URL: {', '.join(matched_kw[:4])}.")
        score += 20
    elif len(matched_kw) == 1:
        reasons.append(f"Suspicious keyword detected in the URL: '{matched_kw[0]}'.")
        score += 10

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

    if len(url) > 150:
        reasons.append("URL is unusually long — sometimes used to obscure the true destination.")
        score += 10

    score = min(score, 100)

    if score >= 60:
        return {"level": "danger",  "score": score, "title": "Dangerous — do not visit this site.",
                "reasons": reasons or ["This URL matches multiple high-risk patterns."]}
    elif score >= 25:
        return {"level": "warning", "score": score, "title": "Suspicious — proceed with extreme caution.",
                "reasons": reasons or ["This URL has characteristics associated with suspicious sites."]}
    else:
        return {"level": "safe",    "score": score, "title": "No threats detected.",
                "reasons": reasons or ["This URL passed all safety checks."]}


# ═════════════════════════════════════════════════════════════════════════════
#  ROUTES
# ═════════════════════════════════════════════════════════════════════════════

@app.route("/")
def home():
    return render_template("landing.html")


# ─── Auth: Sign Up ────────────────────────────────────────────────────────────

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user():
        return redirect(url_for("dashboard"))

    error = None
    form  = {}

    if request.method == "POST":
        name     = request.form.get("name",     "").strip()
        email    = request.form.get("email",    "").strip()
        password = request.form.get("password", "").strip()
        confirm  = request.form.get("confirm",  "").strip()
        form     = {"name": name, "email": email}

        if not name:
            error = "Please enter your name."
        elif not email or "@" not in email:
            error = "Please enter a valid email address."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."
        elif password != confirm:
            error = "Passwords do not match."
        elif find_user_by_email(email):
            error = "An account with that email already exists."
        else:
            users = load_users()
            new_user = {
                "id":         str(uuid.uuid4()),
                "name":       name,
                "email":      email,
                "password":   generate_password_hash(password),
                "bio":        "",
                "joined":     datetime.now().strftime("%Y-%m-%d"),
                "reports":    0,
            }
            users.append(new_user)
            save_users(users)
            session["user_id"] = new_user["id"]
            return redirect(url_for("dashboard"))

    return render_template("signup.html", error=error, form=form)


# ─── Auth: Sign In ────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user():
        return redirect(url_for("dashboard"))

    error = None
    form  = {}

    if request.method == "POST":
        email    = request.form.get("email",    "").strip()
        password = request.form.get("password", "").strip()
        form     = {"email": email}

        if not email or not password:
            error = "Please enter both an email address and a password."
        else:
            user = find_user_by_email(email)
            if user and check_password_hash(user["password"], password):
                session["user_id"] = user["id"]
                return redirect(url_for("dashboard"))
            else:
                error = "Incorrect email or password."

    return render_template("login.html", error=error, form=form)


# ─── Auth: Logout ─────────────────────────────────────────────────────────────

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("home"))


# ─── Profile: View ────────────────────────────────────────────────────────────

@app.route("/profile")
def profile():
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    all_reports = load_reports()
    # Count reports submitted by this user (tracked by user_id field on each report)
    user_reports = [r for r in all_reports if r.get("user_id") == user["id"]]

    return render_template("profile.html", user=user, user_reports=user_reports,
                           total_reports=len(all_reports))


# ─── Profile: Edit ────────────────────────────────────────────────────────────

@app.route("/profile/edit", methods=["POST"])
def profile_edit():
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    action = request.form.get("action", "info")
    users  = load_users()
    idx    = next((i for i, u in enumerate(users) if u["id"] == user["id"]), None)
    if idx is None:
        return redirect(url_for("profile"))

    if action == "info":
        name  = request.form.get("name",  "").strip()
        bio   = request.form.get("bio",   "").strip()
        email = request.form.get("email", "").strip()

        if not name:
            return redirect(url_for("profile") + "?error=Name+cannot+be+empty.")
        if not email or "@" not in email:
            return redirect(url_for("profile") + "?error=Please+enter+a+valid+email.")

        # Check email uniqueness (allow same user keeping their email)
        conflict = find_user_by_email(email)
        if conflict and conflict["id"] != user["id"]:
            return redirect(url_for("profile") + "?error=That+email+is+already+in+use.")

        users[idx]["name"]  = name
        users[idx]["bio"]   = bio
        users[idx]["email"] = email

    elif action == "password":
        current_pw  = request.form.get("current_password", "").strip()
        new_pw      = request.form.get("new_password",     "").strip()
        confirm_pw  = request.form.get("confirm_password", "").strip()

        if not check_password_hash(users[idx]["password"], current_pw):
            return redirect(url_for("profile") + "?error=Current+password+is+incorrect.")
        if len(new_pw) < 8:
            return redirect(url_for("profile") + "?error=New+password+must+be+at+least+8+characters.")
        if new_pw != confirm_pw:
            return redirect(url_for("profile") + "?error=New+passwords+do+not+match.")

        users[idx]["password"] = generate_password_hash(new_pw)

    save_users(users)
    return redirect(url_for("profile") + "?success=1")


# ─── Dashboard ────────────────────────────────────────────────────────────────

@app.route("/dashboard")
def dashboard():
    reports = load_reports()
    recent  = sorted(
        [r for r in reports if r.get("threat_type")],
        key=lambda r: r.get("timestamp", ""),
        reverse=True
    )[:4]
    return render_template(
        "index.html",
        recent_reports=recent,
        total_reports=len(reports),
        tip=get_daily_tip(),
    )


# ─── Scanner ──────────────────────────────────────────────────────────────────

@app.route("/scanner", methods=["GET", "POST"])
def scanner():
    result      = None
    scanned_url = None

    if request.method == "POST":
        url = request.form.get("url", "").strip()

        if not url:
            result = {"level": "error", "title": "Please enter a URL to scan.",
                      "reasons": ["The input field was empty. Enter a full URL starting with http:// or https://"],
                      "score": 0}
        elif not url.startswith(("http://", "https://")):
            result = {"level": "error", "title": "Invalid URL format.",
                      "reasons": ["Please enter a URL beginning with http:// or https://  —  e.g. https://example.com"],
                      "score": 0}
        else:
            try:
                result      = analyse_url(url)
                scanned_url = url
            except Exception:
                result = {"level": "error", "title": "Something went wrong analysing that URL.",
                          "reasons": ["The URL could not be analysed. Please check the format and try again."],
                          "score": 0}

    return render_template("scanner.html", result=result, scanned_url=scanned_url)


# ─── Report ───────────────────────────────────────────────────────────────────

@app.route("/report", methods=["GET", "POST"])
def report():
    error       = None
    form_values = {}

    if request.method == "POST":
        threat_type = request.form.get("threat_type", "").strip()
        url_content = request.form.get("url_content", "").strip()
        description = request.form.get("description", "").strip()

        form_values = {"threat_type": threat_type, "url_content": url_content, "description": description}

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
            user    = current_user()
            new_report = {
                "threat_type": threat_type,
                "url_content": url_content,
                "description": description,
                "timestamp":   datetime.now().strftime("%Y-%m-%d %H:%M"),
                "user_id":     user["id"] if user else None,
                "user_name":   user["name"] if user else "Anonymous",
            }
            reports.append(new_report)
            save_reports(reports)

            # Increment user's report counter
            if user:
                users = load_users()
                for u in users:
                    if u["id"] == user["id"]:
                        u["reports"] = u.get("reports", 0) + 1
                        break
                save_users(users)

            return redirect(url_for("report_success"))

    if not form_values.get("url_content"):
        form_values["url_content"] = request.args.get("url", "")

    return render_template("report.html", error=error, form=form_values)


@app.route("/report/success")
def report_success():
    return render_template("report_success.html")


# ─── Reports list ─────────────────────────────────────────────────────────────

@app.route("/reports")
def reports():
    all_reports = load_reports()
    valid = [r for r in all_reports if r.get("threat_type") or r.get("url_content")]
    valid = sorted(valid, key=lambda r: r.get("timestamp", ""), reverse=True)
    return render_template("reports.html", reports=valid)


# ─── Education ────────────────────────────────────────────────────────────────

@app.route("/education")
def education():
    return render_template("education.html")


# ─── Settings ────────────────────────────────────────────────────────────────

@app.route("/settings")
def settings():
    return render_template("settings.html")


# ─── Error handlers ──────────────────────────────────────────────────────────

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("404.html", code=500), 500


if __name__ == "__main__":
    app.run(debug=True)
