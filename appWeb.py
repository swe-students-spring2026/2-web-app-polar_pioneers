from flask import Flask, flash, redirect, render_template, request, url_for

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev"


# Demo data so templates render without a database/backend yet.
DEMO_RUNS = [
    {
        "_id": "1",
        "title": "OpenAI — Software Engineer",
        "company": "OpenAI",
        "role": "Software Engineer",
        "score": 82,
        "created_at": "2026-02-25",
        "status": "Interview",
        "notes": "Strong backend alignment.",
        "strengths": ["Python", "API design", "Problem solving"],
        "missing_skills": ["Kubernetes", "GraphQL"],
        "suggested_edits": [
            "Quantify impact in 2 bullet points.",
            "Add one cloud deployment example.",
        ],
        "insights": ["Great technical fit.", "Highlight leadership projects."],
    },
    {
        "_id": "2",
        "title": "Stripe — Backend Engineer",
        "company": "Stripe",
        "role": "Backend Engineer",
        "score": 66,
        "created_at": "2026-02-20",
        "status": "Applied",
        "notes": "Need stronger distributed systems examples.",
        "strengths": ["Python", "SQL"],
        "missing_skills": ["Distributed systems"],
        "suggested_edits": ["Add scaling/caching project details."],
        "insights": "Good baseline match with room to improve.",
    },
]


def get_run_or_first(run_id: str):
    for run in DEMO_RUNS:
        if run["_id"] == run_id:
            return run
    return DEMO_RUNS[0]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        flash("Logged in (demo mode).", "success")
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        flash("Account created (demo mode).", "success")
        return redirect(url_for("dashboard"))
    return render_template("signup.html")


@app.route("/logout")
def logout():
    flash("Logged out.", "info")
    return redirect(url_for("index"))


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", runs=DEMO_RUNS)


@app.route("/runs/new", methods=["GET", "POST"])
def new_run():
    if request.method == "POST":
        flash("Analysis submitted (demo mode).", "success")
        return redirect(url_for("dashboard"))
    return render_template("new_run.html")


@app.route("/runs/<run_id>")
def run_detail(run_id: str):
    run = get_run_or_first(run_id)
    return render_template("run_detail.html", run=run)


@app.route("/runs/<run_id>/edit", methods=["GET", "POST"])
def edit_run(run_id: str):
    run = get_run_or_first(run_id)
    if request.method == "POST":
        run["title"] = request.form.get("title", run.get("title", ""))
        run["company"] = request.form.get("company", run.get("company", ""))
        run["role"] = request.form.get("role", run.get("role", ""))
        run["status"] = request.form.get("status", run.get("status", "Draft"))
        run["notes"] = request.form.get("notes", run.get("notes", ""))
        flash("Analysis updated.", "success")
        return redirect(url_for("run_detail", run_id=run_id))
    return render_template("edit_run.html", run=run)


@app.route("/runs/<run_id>/delete", methods=["GET", "POST"])
def delete_run(run_id: str):
    global DEMO_RUNS
    if request.method == "POST":
        DEMO_RUNS = [run for run in DEMO_RUNS if run["_id"] != run_id]
        flash("Analysis deleted.", "success")
        return redirect(url_for("dashboard"))
    run = get_run_or_first(run_id)
    return render_template("delete_confirm.html", run=run)


if __name__ == "__main__":
    app.run(debug=True)
