import asyncio, os
import mongoUser
from datetime import date
from dotenv import load_dotenv
from io import BytesIO
from flask import Flask, redirect, render_template, request, url_for, session
from pypdf import PdfReader
from mongo import initMongo

import parser
import mongoSession


load_dotenv()
initMongo(os.getenv("MONGO_URI"), os.getenv("MONGO_DBNAME", "resumego"))

app = Flask(__name__)

#get the secret key from env
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

def extract_pdf_text(pdf_bytes: bytes) -> str:
    #if the uploaded file is emply, return error
    if not pdf_bytes:
        return "error: input pdf file"
    #conver the pdf into a file object so the pdf reader can read it
    reader = PdfReader(BytesIO(pdf_bytes))
    #go through each page and extract the text, then join all the text into one string
    pages_text = [(page.extract_text() or "").strip() for page in reader.pages]
    return "\n\n".join(text for text in pages_text if text).strip()


@app.route("/")
def index():
    user_id = session.get("user_id")
    login_session_id = session.get("login_session_id")
    #if the user is not logged in or the session is not on, make the session invalid
    if(not user_id or not login_session_id):
        return render_template("index.html", is_valid=False)
    #ensure the session is valid
    is_valid = mongoUser.validateUserLoginSession(user_id, login_session_id)
    if(not is_valid):
        return render_template("index.html", is_valid=False)
    return render_template("index.html", is_valid=True)
    

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").lower()
        password = request.form.get("password","")
        #ensure that both are inputed
      
        if not email or not password:
            return render_template("login.html", is_valid=False)
        result = mongoUser.login(email=email,password=password)
        #check if the login is successful
        if result["status"] == mongoUser.LoginStatus.ERROR_EMAIL_NOT_FOUND:
            return render_template("login.html", is_valid=False)
        if result["status"] == mongoUser.LoginStatus.ERROR_PASSWORD_INCORRECT:
            return render_template("login.html", is_valid=False)
        if result["status"] != mongoUser.LoginStatus.SUCCESS:
            return render_template("login.html", is_valid=False)
        #successful login so store the user info for the session
        session["user_id"] = result["user_id"]
        session["login_session_id"] = result["login_session_id"]
        
        return redirect(url_for("dashboard"))
    return render_template("login.html", is_valid=False)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        #getdata from submitted form
        email = request.form.get("email", "").lower()
        password = request.form.get("password","")
        confirm = request.form.get("confirm_password","")
        #if the inputs are invalid just go back to the screen
        if not email or not password:
            return render_template("signup.html", is_valid=False)
        #check if the 2 passwords are the same
        if password != confirm:
            return render_template("signup.html", is_valid=False)
        result = mongoUser.addUser(email = email, password = password)
        #if email already exist in the database or anything fails
        if result["status"] == mongoUser.AddUserStatus.ERROR_EMAIL_EXISTS_ALREADY:
            return redirect(url_for("login"))
        if result["status"] != mongoUser.AddUserStatus.SUCCESS:
            return render_template("signup.html", is_valid=False)
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
    return render_template("signup.html", is_valid=False)


@app.route("/logout")
def logout():
    #remove session info and go back to the homepage
    session["user_id"] = ""
    session["login_session_id"] = ""
    return redirect(url_for("index"))


@app.route("/dashboard")
def dashboard():
    user_id = session.get("user_id")
    login_session_id = session.get("login_session_id")
    #if no one is logged in go back to login page
    if(not user_id or not login_session_id):
        return redirect(url_for("login"))
    is_valid = mongoUser.validateUserLoginSession(user_id, login_session_id)
    if(not is_valid):
        return redirect(url_for("login"))
    #fetch all the resume analysis runs for this user
    _sessions = mongoSession.getAllSessionsByUser(user_id)
    runs = []
    #go through all the sessions to get the display info
    for _session in _sessions:
        if(_session["status"] == mongoSession.SessionStatus.COMPLETE):
            runs.append({
                "_session_id": _session["session_id"],
                "created_at": _session["input"]["requested_at"].isoformat(),
                "resume_file_name": _session["input"]["resume_file_name"],
                "status": _session["status"].name,
                "job_description": _session["input"]["job_description"],
                "Company_name": _session["input"]["C_name"],
                "notes": _session["input"]["notes"],
                #stuff actually outputed below
                "score": _session["output"]["match_score"],
                "strong_matches": _session["output"]["strong_matches"],
                "missing_skills": _session["output"]["missing_skills"],
                "suggested_edits": _session["output"]["suggested_edits"],
                "ai_insights": _session["output"]["ai_insights"]
            })
        else:
            runs.append({
                #append the basic info for runs that are not completed
                "_session_id": _session["session_id"],
                "created_at": _session["input"]["requested_at"].isoformat(),
                "resume_file_name": _session["input"]["resume_file_name"],
                "status": _session["status"].name,
                "job_description": _session["input"]["job_description"],
                "Company_name": _session["input"]["C_name"],
                "notes": _session["input"]["notes"],
            })
    return render_template("dashboard.html", is_valid=True, runs=runs)


@app.route("/runs/new", methods=["GET", "POST"])
def new_run():
    #redirect to login if login session is not valid
    user_id = session.get("user_id")
    login_session_id=session.get("login_session_id")
    if(not user_id or not login_session_id):
        return redirect(url_for("login"))
    is_valid =mongoUser.validateUserLoginSession(user_id, login_session_id)
    if(not is_valid):
        return redirect(url_for("login"))
    #prepare to pass the info to the agent
    if request.method== "POST":
        notes = request.form.get("notes", "").strip()
        job_description= request.form.get("job_description", "").strip()
        companyName =request.form.get("cName", "").strip()
        #job description is required, redirect back if not provided
        if not job_description:
            return redirect(url_for("new_run"))
        #parsed output will either be structured or none at all
        parsed_output:parser.AgentOutput|None = None
        session_id=""
        try:
            from appRun import ResumeGoRun
            uploaded_file= request.files.get("resume_file")
            resume_filename =uploaded_file.filename if uploaded_file and uploaded_file.filename else "Not provided"
            resume_pdf_bytes = uploaded_file.read()
            extracted_resume_text = extract_pdf_text(resume_pdf_bytes or b"")
            #create a new analysis session in the databse
            session_id = mongoSession.createSession(user_id, job_description, resume_filename, resume_pdf_bytes, "application/pdf", notes, companyName)
            #run the agent
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
            #put the output in structured fields
            parsed_output = parser.parseAgentOutput(result["result"])
            print(parsed_output)
        except Exception as exc:
            #if any error occurs, update the session status in MongoDB
            error_msg = f"Analysis failed: {exc}"
            print(error_msg)
            mongoSession.setSessionError(session_id, error_msg)
            return redirect(url_for("run_detail", run_id=session_id))
        #set error if parsing fails
        if(parsed_output is None):
            mongoSession.setSessionError(session_id, error_msg)
            return redirect(url_for("run_detail", run_id=session_id))
        #store the result in the database
        mongoSession.completeSession(
            session_id,
            parsed_output["match_score"],
            parsed_output["strong_matches"],
            parsed_output["missing_skills"],
            parsed_output["suggested_edits"],
            parsed_output["ai_insights"]
        )
        #return the detailed results page for this run
        return redirect(url_for("run_detail", run_id=session_id))
    #return the new run page otherwise
    return render_template("new_run.html", is_valid=True)

#sample run display
@app.route("/runs/1")
def show_sample():
    run = {
            "session_id": -1,
            "created_at": "",
            "resume_file_name": "Amazon(SAMPLE.pdf)",
            "status": "COMPLETE",
            "job_description": "Amazon sofware engineer",
            "Company_name":"Amazon",
            "notes": "I am super good at coding and Jeff Bethos knows me",
            "score": 92,
            "strong_matches": [
        'Relevant education in Computer Science and Mathematics from a prestigious university.',
        'Strong programming skills in Java, Python, C, and SQL, which are essential for a software engineering role.',
        'Experience in building scalable REST APIs and working with cloud technologies (AWS).',
        'Internship experience in AI and software engineering, demonstrating practical application of skills.',
        'Proven ability to improve system efficiencies and reduce processing times significantly.',
        'Leadership experience as a founder of a project, showcasing initiative and project management skills.'
      ],
            "missing_skills": [
        'Experience with specific Amazon technologies or frameworks (e.g., AWS services beyond basic knowledge).',
        'Familiarity with Agile methodologies or software development lifecycle practices.',
        'Knowledge of front-end technologies (e.g., React, Angular) which may be beneficial for full-stack roles.',
        'Experience with version control systems (e.g., Git) in a collaborative environment.',
        'Soft skills such as teamwork, communication, and problem-solving, which are crucial for a software engineer at Amazon.'
      ],
            "suggested_edits":[
        'Include specific projects or contributions that demonstrate teamwork and collaboration.',
        'Highlight any experience with Agile methodologies or software development processes.',
        'Add a section for certifications or relevant online courses (e.g., AWS Certified Developer).',
        'Consider reformatting the resume for better readability, ensuring consistent bullet point styles and spacing.',
        'Include a brief summary or objective statement at the top to clarify career goals and interest in the Amazon software engineer role.'
      ],
            "ai_insights": "Polar Pioneer's resume showcases a strong foundation in software engineering, particularly in AI and backend development, "
            "which aligns well with the requirements for a software engineer at Amazon. The candidate's experience with building scalable systems and improving efficiencies is a significant asset. "
            "However, to enhance the application, it would be beneficial to emphasize collaborative experiences and familiarity with Agile practices, as these are often critical in large tech companies like Amazon. "
            "Additionally, highlighting any specific experience with Amazon's technology stack or methodologies could further strengthen the application. "
            "Overall, Polar Pioneer presents a solid candidate profile with room for refinement to better match the expectations of the role."
        }
    return render_template("run_detail.html", run=run)
    
    

#retrieving the details of a analysis session
@app.route("/runs/<run_id>")
def run_detail(run_id: str):
    #ensure the login session is valid
    user_id = session.get("user_id")
    login_session_id = session.get("login_session_id")
    if(not user_id or not login_session_id):
        return redirect(url_for("login"))
    is_valid = mongoUser.validateUserLoginSession(user_id, login_session_id)
    if(not is_valid):
        return redirect(url_for("login"))
    #get the session data from mongodb
    _session = mongoSession.getSessionById(run_id)
    #dummy template incase no sessions exist so nothing crashes
    if(_session is None):
        run = {
            "session_id": "",
            "created_at": "",
            "resume_file_name": "Run Does Not Exist",
            "status": "Run Does Not Exist",
            "job_description": "",
            "notes": ""
        }
        return render_template("run_detail.html", run=run)
    if(_session["status"] == mongoSession.SessionStatus.COMPLETE):
        run = {
            "session_id": run_id,
            "created_at": _session["input"]["requested_at"].isoformat(),
            "resume_file_name": _session["input"]["resume_file_name"],
            "status": _session["status"].name,
            "job_description": _session["input"]["job_description"],
            "Company_name": _session["input"]["C_name"],
            "notes": _session["input"]["notes"],
            #stuff actually outputed below
            "score": _session["output"]["match_score"],
            "strong_matches": _session["output"]["strong_matches"],
            "missing_skills": _session["output"]["missing_skills"],
            "suggested_edits": _session["output"]["suggested_edits"],
            "ai_insights": _session["output"]["ai_insights"]
        }
        return render_template("run_detail.html", run=run)
    run = {
        "session_id": run_id,
        "created_at": _session["input"]["requested_at"].isoformat(),
        "resume_file_name": _session["input"]["resume_file_name"],
        "status": _session["status"].name,
        "job_description": _session["input"]["job_description"],
        "Company_name": _session["input"]["C_name"],
        "notes": _session["input"]["notes"],
    }
    #render the page
    return render_template("run_detail.html", is_valid=True, run=run)


if __name__ == "__main__":
    app.run(debug=True)
