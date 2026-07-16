from flask import Flask, render_template, request, redirect, url_for
import json

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("login.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if email and password:
            return redirect(url_for("dashboard"))

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    return render_template("index.html")

@app.route("/scanner", methods=["GET", "POST"])
def scanner():
    result = None

    if request.method == "POST":
        url = request.form.get("url")

        if "http://" in url:
            result = "Warning: Not secure"

        else:
            result = "Safe"

    return render_template("scanner.html", result=result)


@app.route("/report", methods=["GET", "POST"])
def report():

    if request.method == "POST":

        new_report = {
            "title": request.form["title"],
            "description": request.form["description"]
        }

        with open("reports.json", "r") as file:
            reports = json.load(file)

        reports.append(new_report)

        with open("reports.json", "w") as file:
            json.dump(reports, file, indent=4)

        return render_template(
            "report.html",
            success=True
        )

    return render_template(
        "report.html",
        success=False
    )


@app.route("/reports")
def reports():

    with open("reports.json", "r") as file:
        reports = json.load(file)

    return render_template(
        "reports.html",
        reports=reports
    )


@app.route("/education")
def education():
    return render_template("education.html")


if __name__ == "__main__":
    app.run(debug=True)