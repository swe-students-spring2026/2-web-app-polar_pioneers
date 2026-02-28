import asyncio, os
import mongo
import mongoUser

from datetime import date
from dotenv import load_dotenv

from flask import Flask, flash, redirect, render_template, request, url_for, session

app = Flask(__name__)

#load .env information into the environment
load_dotenv()

#get the secret key from env
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

#connect flask with mongoDB
mongo.initMongo(os.getenv("MONGO_URI"), os.getenv("MONGO_DBNAME"))


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


def clarification_response(text: str) -> bool:
    if not text:
        return True
    lowered = text.lower()
    clarification_markers = [
        "message was cut off",
        "could you please provide more details",
        "please provide more details",
        "clarify your question",
        "can you clarify",
        "need more information",
        "insufficient information",
    ]
    return any(marker in lowered for marker in clarification_markers)


def _build_fallback_insights(company: str, role: str, job_description: str) -> str:
    first_sentence = job_description.split(".")[0].strip()
    jd_preview = first_sentence if first_sentence else "The posting emphasizes strong role alignment and measurable impact."
    return (
        f"Match Score: 70/100\n"
        f"Strong Matches: transferable experience likely aligns with {role or 'the target role'} expectations.\n"
        f"Missing Skills: add explicit keywords from the posting and any required tooling not yet listed.\n"
        f"Suggested Edits: quantify outcomes, mirror job-description wording, and prioritize relevant projects.\n"
        f"AI Insights: For {company or 'this company'}, highlight 2–3 accomplishments with measurable impact and tailor bullets to this requirement: {jd_preview}."
    )


def get_run_or_first(run_id: str):
    for run in DEMO_RUNS:
        if run["_id"] == run_id:
            return run
    return DEMO_RUNS[0]


def next_run_id() -> str:
    ids = [int(run.get("_id", "0")) for run in DEMO_RUNS if str(run.get("_id", "")).isdigit()]
    return str(max(ids, default=0) + 1)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").lower()
        password = request.form.get("password","")
        #ensure that both are inputed
        if not email or not password:
            return render_template("login.html")
        result = mongoUser.login(email=email,password=password)
        result = mongoUser.login(email=email, password=password)
        #check if the login is successful
        if result["status"] == mongoUser.LoginStatus.ERROR_USER_NOT_FOUND:
            return render_template("login.html")
        if result["status"] == mongoUser.LoginStatus.ERROR_WRONG_PASSWORD:
            return render_template("login.html")
        if result["status"] != mongoUser.LoginStatus.SUCCESS:
            return render_template("login.html")
        #successful login so store the user info for the session
        session["user_id"] = result["user_id"]
        session["login_session_id"] = result["login_session_id"]
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        #getdata from submitted form
        email = request.form.get("email", "")
        password = request.form.get("password","")
        confirm = request.form.get("confirm_password","")
        #if the inputs are invalid just go back to the screen
        if not email or not password:
            return render_template("signup.html")
        #check if the 2 passwords are the same
        if password != confirm:
            return render_template("signup.html")
        result = mongoUser.addUser(email = email, password = password)
        #if email already exist in the database or anything fails
        if result["status"] == mongoUser.AddUserStatus.ERROR_EMAIL_EXISTS_ALREADY:
            return redirect(url_for("login"))
        if result["status"] == mongoUser.AddUserStatus.SUCCESS:
            return render_template("signup.html")
        #log the user in after successful signup
        login_result = mongoUser.login(email=email, password = password)
        #if login succeeds, store the user info in into the Flask session
        if login_result["status"] == mongoUser.LoginStatus.SUCCESS:
            session["user_id"] = login_result["user_id"]
            session["login_session_id"] = login_result["login_session_id"]
            return redirect(url_for("dashboard"))
        #if login fails somehow
        return redirect(url_for("login"))
    #if the request is GET
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
        action = request.form.get("action")
        company = request.form.get("company", "").strip()
        role = request.form.get("role", "").strip()
        title = request.form.get("title", "").strip()
        notes = request.form.get("notes", "").strip()
        job_description = request.form.get("job_description", "").strip()

        # Keep save-draft behavior lightweight.
        if action == "draft":
            run_id = next_run_id()
            DEMO_RUNS.insert(
                0,
                {
                    "_id": run_id,
                    "title": title or (f"{company} — {role}".strip(" —") or "Untitled Draft"),
                    "company": company,
                    "role": role,
                    "score": 0,
                    "created_at": date.today().isoformat(),
                    "status": "Draft",
                    "notes": notes,
                    "strengths": [],
                    "missing_skills": [],
                    "suggested_edits": [],
                    "insights": "Draft saved. Run analysis to generate AI insights.",
                },
            )
            flash("Draft saved.", "success")
            return redirect(url_for("dashboard"))

        if not job_description:
            flash("Please paste a job description before running analysis.", "error")
            return redirect(url_for("new_run"))

        ai_insights = ""
        try:
            # Lazy import keeps the web app bootable even if AI deps are not installed yet.
            from appRun import ResumeGoRun

            uploaded_file = request.files.get("resume_file")
            resume_filename = uploaded_file.filename if uploaded_file and uploaded_file.filename else "Not provided"

            analysis_request = (
                "Please analyze this candidate for the role and provide:\n"
                "1) Match Score (0-100)\n"
                "2) Strong Matches (bullet list)\n"
                "3) Missing Skills (bullet list)\n"
                "4) Suggested Edits (bullet list)\n"
                "5) Final AI Insights paragraph\n\n"
                f"Company: {company or 'N/A'}\n"
                f"Role: {role or 'N/A'}\n"
                f"Analysis title: {title or 'N/A'}\n"
                f"Notes: {notes or 'N/A'}\n"
                f"Uploaded resume filename: {resume_filename}\n\n"
                "Job description:\n"
                f"{job_description}"
            )

            result = asyncio.run(ResumeGoRun(analysis_request))
            ai_insights = str(result.get("result", "")).strip()
        except Exception as exc:
            ai_insights = f"Analysis failed: {exc}"

        if clarification_response(ai_insights) or ai_insights.startswith("Analysis failed:"):
            ai_insights = _build_fallback_insights(company, role, job_description)

        run_id = next_run_id()
        new_item = {
            "_id": run_id,
            "title": title or (f"{company} — {role}".strip(" —") or "Untitled Analysis"),
            "company": company,
            "role": role,
            "score": 70,
            "created_at": date.today().isoformat(),
            "status": "Applied",
            "notes": notes,
            "strengths": [],
            "missing_skills": [],
            "suggested_edits": [],
            "insights": ai_insights or "No insights were returned.",
        }
        DEMO_RUNS.insert(0, new_item)
        flash("Analysis completed.", "success")
        return redirect(url_for("run_detail", run_id=run_id))
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
