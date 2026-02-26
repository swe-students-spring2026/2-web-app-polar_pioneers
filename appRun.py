from agent import ResumeAgent
import asyncio
from state import AppState
from langgraph.graph import StateGraph, START, END

async def ResumeGoRun(user_input: str):

    agentNode  = ResumeAgent(
        prompt=(
            "You are an expert resume reviewer. Analyze the provided information and return helpful, specific feedback. "
            "If resume details are incomplete, make reasonable assumptions and still provide an answer. "
            "Do not ask the user to clarify or provide more details. "
            "Return concise sections: Match Score (0-100), Strong Matches, Missing Skills, Suggested Edits, and AI Insights."
        ),
        user_input=user_input,
    )

    
    workflow = StateGraph(AppState)
    workflow.add_node("chat", agentNode)

  
    workflow.add_edge(START, "chat")
    workflow.add_edge("chat", END)
   
   
    resumeGo  = workflow.compile()
    return await resumeGo.ainvoke(AppState(user_input=user_input))
    
if __name__ == "__main__":
    import asyncio
    output = asyncio.run(ResumeGoRun("Give a rating(100 points scale)of my resume as NYU supersmart student and intern at nvidia before for software engineer. Also, I have 3 AI robotic labs experiences."))
    #I used this fixed input for demo, it will later on be the AppState(check state.py) object that load the pdf from our frontend website
    print(output['result'])


# to run this on your terminal: 
# pipenv shell
# pipenv run python appRun.py