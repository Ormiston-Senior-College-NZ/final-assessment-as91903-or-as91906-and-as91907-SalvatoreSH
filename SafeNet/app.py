import os
import re
import uuid
import time
import sqlite3
from datetime import datetime
from urllib.parse import urlparse, quote_plus
from functools import wraps
from contextlib import contextmanager
from flask import (Flask, render_template, request, redirect,
                   url_for, session, jsonify)
from werkzeug.security import generate_password_hash, check_password_hash

# ═══════════════════════════════════════════════════════════════════════════
#  APP SETUP
# ═══════════════════════════════════════════════════════════════════════════

app = Flask(__name__, static_folder="Static", template_folder="templates")
app.secret_key = os.environ.get("SAFENET_SECRET", "safenet-dev-secret-change-in-prod")
app.jinja_env.filters["urlencode"] = lambda s: quote_plus(str(s))

DB_PATH = os.path.join(os.path.dirname(__file__), "safenet.db")


# ═══════════════════════════════════════════════════════════════════════════
#  DATABASE
# ═══════════════════════════════════════════════════════════════════════════

@contextmanager
def get_db():
    """Yield a connected, row_factory-enabled SQLite connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # access columns by name
    conn.execute("PRAGMA journal_mode=WAL") # safe concurrent writes
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create tables if they don't exist yet."""
    with get_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id           TEXT PRIMARY KEY,
                name         TEXT NOT NULL,
                email        TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password     TEXT NOT NULL,
                bio          TEXT DEFAULT '',
                joined       TEXT NOT NULL,
                report_count INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS reports (
                id           TEXT PRIMARY KEY,
                threat_type  TEXT NOT NULL,
                url_content  TEXT NOT NULL,
                description  TEXT NOT NULL,
                timestamp    TEXT NOT NULL,
                user_id      TEXT,
                user_name    TEXT DEFAULT 'Anonymous',
                flagged      INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS scan_history (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    TEXT NOT NULL,
                url        TEXT NOT NULL,
                level      TEXT NOT NULL,
                score      INTEGER NOT NULL,
                scanned_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE INDEX IF NOT EXISTS idx_reports_type      ON reports(threat_type);
            CREATE INDEX IF NOT EXISTS idx_reports_timestamp ON reports(timestamp);
            CREATE INDEX IF NOT EXISTS idx_scan_history_user ON scan_history(user_id);
        """)


# ═══════════════════════════════════════════════════════════════════════════
#  RATE LIMITING  (in-memory, per IP)
# ═══════════════════════════════════════════════════════════════════════════

_rate_store: dict = {}


def _rate_key(action: str) -> str:
    ip = request.headers.get(
        "X-Forwarded-For", request.remote_addr or "unknown"
    ).split(",")[0].strip()
    return f"{action}:{ip}"


def rate_limited(action: str, limit: int, window: int):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if request.method != "POST":
                return fn(*args, **kwargs)
            key  = _rate_key(action)
            now  = time.time()
            hits = [t for t in _rate_store.get(key, []) if now - t < window]
            if len(hits) >= limit:
                retry = int(window - (now - hits[0])) + 1
                return render_template(
                    "404.html", code=429,
                    message=f"Too many requests. Please wait {retry} seconds before trying again."
                ), 429
            hits.append(now)
            _rate_store[key] = hits
            return fn(*args, **kwargs)
        return wrapper
    return decorator


# ═══════════════════════════════════════════════════════════════════════════
#  AUTH HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user():
            return redirect(url_for("login") + "?next=" + request.path)
        return fn(*args, **kwargs)
    return wrapper


def find_user_by_email(email: str):
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM users WHERE email = ?", (email.lower(),)
        ).fetchone()
    return dict(row) if row else None


def find_user_by_id(uid: str):
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM users WHERE id = ?", (uid,)
        ).fetchone()
    return dict(row) if row else None


def current_user():
    uid = session.get("user_id")
    return find_user_by_id(uid) if uid else None


@app.context_processor
def inject_user():
    return {"current_user": current_user()}


# ═══════════════════════════════════════════════════════════════════════════
#  DAILY TIPS
# ═══════════════════════════════════════════════════════════════════════════

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
    "A padlock icon means the connection is encrypted, not that the site is safe.",
    "If unsure about a call, hang up and call the company back on their official number.",
]


def get_daily_tip():
    return TIPS[datetime.now().timetuple().tm_yday % len(TIPS)]


# ═══════════════════════════════════════════════════════════════════════════
#  URL ANALYSER
# ═══════════════════════════════════════════════════════════════════════════

def analyse_url(url: str) -> dict:
    reasons   = []
    score     = 0
    url_lower = url.lower()

    if url_lower.startswith("http://"):
        reasons.append("Uses unencrypted HTTP — the connection is not secure.")
        score += 20

    BAD_TLDS = [".tk",".ml",".ga",".cf",".gq",".xyz",".top",".click",
                ".loan",".work",".zip",".ru",".su",".pw",".cc",".biz"]
    for tld in BAD_TLDS:
        if tld in url_lower:
            reasons.append(
                f"Uses a high-risk domain extension ({tld}) commonly associated with scam sites."
            )
            score += 25
            break

    if re.match(r"https?://(\d{1,3}\.){3}\d{1,3}", url):
        reasons.append("Uses a raw IP address as the domain — a common phishing technique.")
        score += 35

    TRUSTED_BRANDS = [
        "paypal","anz","bnz","westpac","kiwibank","asb","nzpost",
        "google","microsoft","apple","amazon","facebook","instagram",
        "netflix","discord","steam","myir","ird","govt","acc",
        "inland-revenue","nzta","msd","servicenow",
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
                        f"Subdomain spoofing — '{brand}' appears as a subdomain of an unrelated domain."
                    )
                    score += 40
                    break
    except Exception:
        pass

    BAD_KEYWORDS = [
        "login","verify","secure","update","confirm","account","banking",
        "password","credential","signin","free-prize","win-prize","claim-now",
        "urgent","suspended","unusual-activity","alert","locked","reactivate",
    ]
    matched_kw = [kw for kw in BAD_KEYWORDS if kw in url_lower]
    if len(matched_kw) >= 2:
        reasons.append(
            f"Multiple suspicious keywords in the URL: {', '.join(matched_kw[:4])}."
        )
        score += 20
    elif matched_kw:
        reasons.append(f"Suspicious keyword in the URL: '{matched_kw[0]}'.")
        score += 10

    SHORTENERS = ["bit.ly","tinyurl.com","t.co","goo.gl","ow.ly",
                  "short.link","rb.gy","cutt.ly","is.gd"]
    for s in SHORTENERS:
        if s in url_lower:
            reasons.append(
                "Shortened URL — the true destination is hidden. "
                "Shortened links are frequently used to disguise malicious sites."
            )
            score += 15
            break

    try:
        if len(urlparse(url).hostname.split(".")) > 4:
            reasons.append(
                "Unusually deep subdomain chain — used to bury the real domain."
            )
            score += 15
    except Exception:
        pass

    if len(url) > 150:
        reasons.append("URL is unusually long — sometimes used to obscure the destination.")
        score += 10

    score = min(score, 100)

    if score >= 60:
        return {"level": "danger",  "score": score,
                "title": "Dangerous — do not visit this site.",
                "reasons": reasons or ["This URL matches multiple high-risk patterns."]}
    elif score >= 25:
        return {"level": "warning", "score": score,
                "title": "Suspicious — proceed with extreme caution.",
                "reasons": reasons or ["This URL has characteristics associated with suspicious sites."]}
    else:
        return {"level": "safe",    "score": score,
                "title": "No threats detected.",
                "reasons": reasons or ["This URL passed all safety checks."]}


# ═══════════════════════════════════════════════════════════════════════════
#  ROUTES — PUBLIC
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/")
def home():
    return render_template("landing.html")


@app.route("/signup", methods=["GET", "POST"])
@rate_limited("signup", limit=5, window=300)
def signup():
    if current_user():
        return redirect(url_for("dashboard"))

    error = None
    form  = {}

    if request.method == "POST":
        name     = request.form.get("name",     "").strip()
        email    = request.form.get("email",    "").strip().lower()
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
            uid = str(uuid.uuid4())
            with get_db() as db:
                db.execute(
                    """INSERT INTO users (id, name, email, password, bio, joined, report_count)
                       VALUES (?, ?, ?, ?, '', ?, 0)""",
                    (uid, name, email,
                     generate_password_hash(password),
                     datetime.now().strftime("%Y-%m-%d"))
                )
            session["user_id"] = uid
            return redirect(url_for("dashboard"))

    return render_template("signup.html", error=error, form=form)


@app.route("/login", methods=["GET", "POST"])
@rate_limited("login", limit=10, window=300)
def login():
    if current_user():
        return redirect(url_for("dashboard"))

    error = None
    form  = {}

    if request.method == "POST":
        email    = request.form.get("email",    "").strip().lower()
        password = request.form.get("password", "").strip()
        form     = {"email": email}

        if not email or not password:
            error = "Please enter both your email address and password."
        else:
            user = find_user_by_email(email)
            if user and check_password_hash(user["password"], password):
                session["user_id"] = user["id"]
                next_url = request.args.get("next") or url_for("dashboard")
                return redirect(next_url)
            else:
                error = "Incorrect email or password."

    return render_template("login.html", error=error, form=form)


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("home"))


# ═══════════════════════════════════════════════════════════════════════════
#  ROUTES — PROTECTED
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/dashboard")
@login_required
def dashboard():
    with get_db() as db:
        total_reports = db.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
        recent_reports = [
            dict(r) for r in db.execute(
                "SELECT * FROM reports ORDER BY timestamp DESC LIMIT 4"
            ).fetchall()
        ]
    return render_template(
        "index.html",
        recent_reports=recent_reports,
        total_reports=total_reports,
        tip=get_daily_tip(),
    )


@app.route("/profile")
@login_required
def profile():
    user = current_user()
    with get_db() as db:
        user_reports = [
            dict(r) for r in db.execute(
                "SELECT * FROM reports WHERE user_id = ? ORDER BY timestamp DESC",
                (user["id"],)
            ).fetchall()
        ]
        total_reports = db.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
        scan_history  = [
            dict(r) for r in db.execute(
                """SELECT url, level, score, scanned_at
                   FROM scan_history WHERE user_id = ?
                   ORDER BY scanned_at DESC LIMIT 10""",
                (user["id"],)
            ).fetchall()
        ]
    return render_template(
        "profile.html",
        user=user,
        user_reports=user_reports,
        total_reports=total_reports,
        scan_history=scan_history,
    )


@app.route("/profile/edit", methods=["POST"])
@login_required
def profile_edit():
    user   = current_user()
    action = request.form.get("action", "info")

    if action == "info":
        name  = request.form.get("name",  "").strip()
        bio   = request.form.get("bio",   "").strip()
        email = request.form.get("email", "").strip().lower()

        if not name:
            return redirect(url_for("profile") + "?error=Name+cannot+be+empty.")
        if not email or "@" not in email:
            return redirect(url_for("profile") + "?error=Please+enter+a+valid+email.")

        conflict = find_user_by_email(email)
        if conflict and conflict["id"] != user["id"]:
            return redirect(url_for("profile") + "?error=That+email+is+already+in+use.")

        with get_db() as db:
            db.execute(
                "UPDATE users SET name=?, bio=?, email=? WHERE id=?",
                (name, bio, email, user["id"])
            )

    elif action == "password":
        current_pw = request.form.get("current_password", "").strip()
        new_pw     = request.form.get("new_password",     "").strip()
        confirm_pw = request.form.get("confirm_password", "").strip()

        if not check_password_hash(user["password"], current_pw):
            return redirect(url_for("profile") + "?error=Current+password+is+incorrect.")
        if len(new_pw) < 8:
            return redirect(url_for("profile") + "?error=New+password+must+be+at+least+8+characters.")
        if new_pw != confirm_pw:
            return redirect(url_for("profile") + "?error=New+passwords+do+not+match.")

        with get_db() as db:
            db.execute(
                "UPDATE users SET password=? WHERE id=?",
                (generate_password_hash(new_pw), user["id"])
            )

    return redirect(url_for("profile") + "?success=1")


@app.route("/settings")
@login_required
def settings():
    return render_template("settings.html")


# ═══════════════════════════════════════════════════════════════════════════
#  ROUTES — SEMI-PUBLIC
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/scanner", methods=["GET", "POST"])
@rate_limited("scan", limit=30, window=60)
def scanner():
    result      = None
    scanned_url = None

    if request.method == "POST":
        url = request.form.get("url", "").strip()

        if not url:
            result = {"level": "error", "score": 0,
                      "title": "Please enter a URL to scan.",
                      "reasons": ["The input was empty. Enter a full URL starting with http:// or https://"]}
        elif not url.startswith(("http://", "https://")):
            result = {"level": "error", "score": 0,
                      "title": "Invalid URL format.",
                      "reasons": ["Please enter a URL beginning with http:// or https://"]}
        else:
            try:
                result      = analyse_url(url)
                scanned_url = url
                _save_scan_history(url, result)
            except Exception:
                result = {"level": "error", "score": 0,
                          "title": "Something went wrong analysing that URL.",
                          "reasons": ["Check the format and try again."]}

    return render_template("scanner.html", result=result, scanned_url=scanned_url)


def _save_scan_history(url: str, result: dict):
    user = current_user()
    if not user:
        return
    with get_db() as db:
        # Remove previous entry for the same URL from this user
        db.execute(
            "DELETE FROM scan_history WHERE user_id=? AND url=?",
            (user["id"], url)
        )
        # Insert fresh entry
        db.execute(
            """INSERT INTO scan_history (user_id, url, level, score, scanned_at)
               VALUES (?, ?, ?, ?, ?)""",
            (user["id"], url,
             result.get("level"), result.get("score"),
             datetime.now().strftime("%Y-%m-%d %H:%M"))
        )
        # Keep only last 20 per user
        db.execute(
            """DELETE FROM scan_history
               WHERE user_id=? AND id NOT IN (
                   SELECT id FROM scan_history
                   WHERE user_id=? ORDER BY scanned_at DESC LIMIT 20
               )""",
            (user["id"], user["id"])
        )


@app.route("/api/scan-history")
def api_scan_history():
    user = current_user()
    if not user:
        return jsonify([])
    with get_db() as db:
        rows = db.execute(
            """SELECT url, level, score, scanned_at as timestamp
               FROM scan_history WHERE user_id=?
               ORDER BY scanned_at DESC LIMIT 20""",
            (user["id"],)
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/report", methods=["GET", "POST"])
@rate_limited("report", limit=10, window=300)
def report():
    error       = None
    form_values = {}

    if request.method == "POST":
        threat_type = request.form.get("threat_type", "").strip()
        url_content = request.form.get("url_content", "").strip()
        description = request.form.get("description", "").strip()
        form_values = {"threat_type": threat_type,
                       "url_content": url_content,
                       "description": description}

        if not threat_type:
            error = "Please select a threat type."
        elif threat_type not in ("phishing", "scam", "malware", "other"):
            error = "Invalid threat type selected."
        elif not url_content:
            error = "Please enter the suspicious URL or message content."
        elif len(url_content) > 2000:
            error = "URL / content must be 2000 characters or fewer."
        elif len(description) < 20:
            error = "Please describe the threat in at least 20 characters."
        elif len(description) > 500:
            error = "Description must be 500 characters or fewer."
        else:
            # Duplicate check
            with get_db() as db:
                dup = db.execute(
                    """SELECT id FROM reports
                       WHERE LOWER(url_content)=LOWER(?)
                       ORDER BY timestamp DESC LIMIT 1""",
                    (url_content,)
                ).fetchone()

            if dup:
                error = "This URL or content has already been reported. Thank you!"
            else:
                user = current_user()
                rid  = str(uuid.uuid4())
                with get_db() as db:
                    db.execute(
                        """INSERT INTO reports
                           (id, threat_type, url_content, description,
                            timestamp, user_id, user_name, flagged)
                           VALUES (?,?,?,?,?,?,?,0)""",
                        (rid, threat_type, url_content, description,
                         datetime.now().strftime("%Y-%m-%d %H:%M"),
                         user["id"]   if user else None,
                         user["name"] if user else "Anonymous")
                    )
                    if user:
                        db.execute(
                            "UPDATE users SET report_count = report_count + 1 WHERE id=?",
                            (user["id"],)
                        )
                return redirect(url_for("report_success"))

    if not form_values.get("url_content"):
        form_values["url_content"] = request.args.get("url", "")

    return render_template("report.html", error=error, form=form_values)


@app.route("/report/success")
def report_success():
    return render_template("report_success.html")


@app.route("/reports")
def reports():
    filter_type = request.args.get("type", "").strip().lower()
    query       = request.args.get("q",    "").strip()

    sql    = "SELECT * FROM reports WHERE 1=1"
    params = []

    if filter_type and filter_type != "all":
        sql    += " AND LOWER(threat_type) = ?"
        params.append(filter_type)

    if query:
        sql    += """ AND (
                        LOWER(url_content)  LIKE ?
                     OR LOWER(description)  LIKE ?
                     OR LOWER(threat_type)  LIKE ?
                  )"""
        q = f"%{query.lower()}%"
        params.extend([q, q, q])

    sql += " ORDER BY timestamp DESC"

    with get_db() as db:
        rows = [dict(r) for r in db.execute(sql, params).fetchall()]

    return render_template(
        "reports.html",
        reports=rows,
        filter_type=filter_type,
        query=query,
    )


@app.route("/education")
def education():
    return render_template("education.html")


# ═══════════════════════════════════════════════════════════════════════════
#  ERROR HANDLERS
# ═══════════════════════════════════════════════════════════════════════════

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html", code=404,
                           message="That page doesn't exist."), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("404.html", code=500,
                           message="Something went wrong on our end. Please try again."), 500

@app.errorhandler(429)
def too_many_requests(e):
    return render_template("404.html", code=429,
                           message="Too many requests. Please slow down and try again."), 429


# ═══════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    init_db()   # create tables on first run
    app.run(debug=True)
