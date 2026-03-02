from agent import ResumeAgent
import asyncio
from state import AppState
from langgraph.graph import StateGraph, START, END

async def ResumeGoRun(
    user_input: str,
    resume_file_name: str | None = None,
    resume_pdf_bytes: bytes | None = None,
    job_description: str | None = None,
    notes: str | None = None,
):

    agentNode  = ResumeAgent(
        prompt=(
            "You are an expert resume reviewer. Analyze the provided information and return helpful, specific feedback. "
            "If resume details are incomplete, make reasonable assumptions and still provide an answer. "
            "Do not ask the user to clarify or provide more details. "
            "Return concise sections: Match Score (0-100), Strong Matches, Missing Skills, Suggested Edits, and AI Insights."
        ),
    )

    
    workflow = StateGraph(AppState)
    workflow.add_node("chat", agentNode)

  
    workflow.add_edge(START, "chat")
    workflow.add_edge("chat", END)
   
   
    resumeGo  = workflow.compile()
    return await resumeGo.ainvoke(
        AppState(
            user_input=user_input,
            resume_file_name=resume_file_name,
            resume_pdf_bytes=resume_pdf_bytes,
            job_description=job_description,
            notes=notes,
        )
    )
    
if __name__ == "__main__":
    import asyncio
    output = asyncio.run(
        ResumeGoRun(
            "Give a rating (100 points scale) of my resume as an NYU student and former NVIDIA software engineering intern. Also, I have 3 AI robotics lab experiences.",
            resume_file_name="sample_resume.pdf",
            resume_pdf_bytes=b"%PDF-1.4 sample",
            job_description="Software Engineer role requiring Python, backend APIs, and ML exposure.",
            notes="Prioritize concise feedback and concrete edits.",
        )
    )
    #I used this fixed input for demo, it will later on be the AppState(check state.py) object that load the pdf from our frontend website
    print(output['result'])


# to run this on your terminal: 
# pipenv shell
# pipenv run python appRun.py