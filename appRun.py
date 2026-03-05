from agent import ResumeAgent
import asyncio  # Needed to run the async ResumeGoRun() entry point from this standalone script.
from state import AppState
from langgraph.graph import StateGraph, START, END #this is the workflow that will pass Agent STATE and update variables of it



async def ResumeGoRun(
    user_input: str,
    resume_file_name: str | None = None,
    resume_pdf_bytes: bytes | None = None,
    job_description: str | None = None,
    notes: str | None = None,
):
    #create an state that store resume analysis inputs for each run
    userState= AppState(
            user_input=user_input, #resume content
            resume_file_name=resume_file_name,
            resume_pdf_bytes=resume_pdf_bytes,
            job_description=job_description,
            notes=notes,
        )
    agentNode  = ResumeAgent( # this node is set in workflow to pass State in to analysis resume with agent
        prompt=(
            "You are an expert resume reviewer. Analyze the provided information and return helpful, specific feedback. "
            "If resume details are incomplete, make reasonable assumptions and still provide an answer. "
            "Do not ask the user to clarify or provide more details. "
            "Return concise sections: Match Score (0-100), Strong Matches, Missing Skills, Suggested Edits, and AI Insights. The score 1-100 should be very diverse and reasonable"
        ), state=userState
    )

    
    workflow = StateGraph(AppState) #state is the main input/output for my langgraph workflow
    workflow.add_node("chat", agentNode)

  
    workflow.add_edge(START, "chat")
    workflow.add_edge("chat", END) #the goal is to put all the anaysis input and store agent output in state.result 
   
   
    resumeGo  = workflow.compile()
    return await resumeGo.ainvoke(userState) #this will return the entire updated state(AppState) object
    


if __name__ == "__main__":
    import asyncio  # to create/manage the event loop for testing for this file.
    from pypdf import PdfReader
    from io import BytesIO

###this is the test run for this appRun.py, you can import your own pdf resume files to see the output from my agent on your on terminal
    def _extract_pdf_text(pdf_bytes: bytes) -> str:
        if not pdf_bytes:
            return "pdf uploading error, make sure it's a pdf file!"

        reader = PdfReader(BytesIO(pdf_bytes))
        pages_text = [(page.extract_text() or "").strip() for page in reader.pages]
        return "\n\n".join(text for text in pages_text if text).strip()

    file_path="~/Desktop/filename.pdf"
    with open(file_path, 'rb') as f:
         resume_pdf_bytes = f.read()

    extracted_resume_text = _extract_pdf_text(resume_pdf_bytes or b"")

    output = asyncio.run(
        ResumeGoRun(
            user_input=extracted_resume_text,
            resume_file_name="_Blake Chang's Resume.pdf",
            resume_pdf_bytes=b"empty for demo run",
            job_description="Software Engineer role requiring Python, backend APIs, and ML exposure.",
            notes="Prioritize concise feedback and concrete edits.",
        )
    )
    #I used this fixed input for demo, it will later on be the AppState(check state.py) object that load the pdf from our frontend website
    print(output['result'])


# to run this on your terminal: 
# pipenv shell
# pipenv run python appRun.py