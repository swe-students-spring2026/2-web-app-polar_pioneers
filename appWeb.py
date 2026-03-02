import asyncio, os
import mongo
import mongoUser
from datetime import date
from dotenv import load_dotenv
from io import BytesIO
from flask import Flask, flash, redirect, render_template, request, url_for, session
from pypdf import PdfReader
from mongo import initMongo

import parser
import mongoSession


load_dotenv()
# initMongo(os.getenv("MONGO_URI"), os.getenv("MONGO_DBNAME", "resumego"))
initMongo("mongodb://localhost:27017/", os.getenv("MONGO_DBNAME", "resumego"))

app = Flask(__name__)

#get the secret key from env
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")



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


def _extract_pdf_text(pdf_bytes: bytes) -> str:
    if not pdf_bytes:
        return "pdf uploading error, make sure it's a pdf file!"

    reader = PdfReader(BytesIO(pdf_bytes))
    pages_text = [(page.extract_text() or "").strip() for page in reader.pages]
    return "\n\n".join(text for text in pages_text if text).strip()


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
        #check if the login is successful
        if result["status"] == mongoUser.LoginStatus.ERROR_EMAIL_NOT_FOUND:
            return render_template("login.html")
        if result["status"] == mongoUser.LoginStatus.ERROR_PASSWORD_INCORRECT:
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
    return render_template("dashboard.html", runs=[]) # TODO: call mongo get sessions


@app.route("/runs/new", methods=["GET", "POST"])
def new_run():
    if request.method == "POST":
        notes = request.form.get("notes", "").strip()
        job_description = request.form.get("job_description", "").strip()

        if not job_description:
            flash("Please paste a job description before running analysis.", "error")
            return redirect(url_for("new_run"))

        parsed_output: parser.AgentOutput | None = None
        session_id = ""
        try:
            # Lazy import keeps the web app bootable even if AI deps are not installed yet.
            from appRun import ResumeGoRun

            uploaded_file = request.files.get("resume_file")
            resume_filename = uploaded_file.filename if uploaded_file and uploaded_file.filename else "Not provided"
            resume_pdf_bytes = uploaded_file.read() 
            extracted_resume_text = _extract_pdf_text(resume_pdf_bytes or b"")

            session_id = mongoSession.createSession("blah", job_description, resume_filename, resume_pdf_bytes, "application/pdf", notes)

            result = asyncio.run(
                ResumeGoRun(
                    user_input=extracted_resume_text,
                    resume_file_name=resume_filename,
                    resume_pdf_bytes=bytes(),
                    job_description=job_description,
                    notes=notes,
                )
            )


            """result is the ouput of our ResumeAgent, need to break the text down to:
            score,match_score,strong_matches,missing_skills,suggested_edits,ai_insights"""

            print(result["result"])
            parsed_output = parser.parseAgentOutput(result["result"])
            print(parsed_output)
        except Exception as exc:
            error_msg = f"Analysis failed: {exc}"
            print(error_msg)
            mongoSession.setSessionError(session_id, error_msg)
            return redirect(url_for("run_detail", run_id=session_id))

        if(parsed_output is None):
            mongoSession.setSessionError(session_id, error_msg)
            return redirect(url_for("run_detail", run_id=session_id))

        mongoSession.completeSession(
            session_id,
            parsed_output["match_score"],
            parsed_output["strong_matches"],
            parsed_output["missing_skills"],
            parsed_output["suggested_edits"],
            parsed_output["ai_insights"]
        )

        # flash("Analysis completed.", "success")
        return redirect(url_for("run_detail", run_id=session_id))
    return render_template("new_run.html")


@app.route("/runs/<run_id>")
def run_detail(run_id: str):
    session = mongoSession.getSessionById(run_id)
    if(session is None):
        run = {
            "session_id": "",
            "created_at": "",
            "resume_file_name": "Run Does Not Exist",
            "status": "Run Does Not Exist",
            "job_description": "",
            "notes": ""
        }
        return render_template("run_detail.html", run=run)
        
    if(session["status"] == mongoSession.SessionStatus.COMPLETE):
        run = {
            "session_id": run_id,
            "created_at": session["input"]["requested_at"].isoformat(),
            "resume_file_name": session["input"]["resume_file_name"],
            "status": session["status"].name,
            "job_description": session["input"]["job_description"],
            "notes": session["input"]["notes"],
            "score": session["output"]["match_score"],
            "strong_matches": session["output"]["strong_matches"],
            "missing_skills": session["output"]["missing_skills"],
            "suggested_edits": session["output"]["suggested_edits"],
            "ai_insights": session["output"]["ai_insights"]
        }
        return render_template("run_detail.html", run=run)
    run = {
        "session_id": run_id,
        "created_at": session["input"]["requested_at"].isoformat(),
        "resume_file_name": session["input"]["resume_file_name"],
        "status": session["status"].name,
        "job_description": session["input"]["job_description"],
        "notes": session["input"]["notes"],
    }
    return render_template("run_detail.html", run=run)


if __name__ == "__main__":
    app.run(debug=True)
