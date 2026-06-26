from flask import Flask, render_template, request
import json

app = Flask(__name__)

@app.route("/")
def home():
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


# BUG 3
# Missing POST support

@app.route("/report")
def report():
    return render_template("report.html")


# BUG 4
# reports.json doesn't exist

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