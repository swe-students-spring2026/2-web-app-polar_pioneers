from agent import ResumeAgent
import asyncio
from state import AppState
from langgraph.graph import StateGraph, START, END

async def ResumeGoRun(user_input: str):

    agentNode  = ResumeAgent(prompt="reply question for resume, if no reseume added, just assume one", user_input=user_input)
    # checkerNode = OutputChecker(prompt=CHECKER_PROMPT)
    
    workflow = StateGraph(AppState)
    workflow.add_node("chat", agentNode)

  
    workflow.add_edge(START, "chat")

    # workflow.add_conditional_edges(
    #     "verify", 
    #     router, 
    #     {
    #         "display": "display",
    #         "client": "client"
    #     }
    # )
    # # workflow.set_finish_point(END)  # <-- Add this line
    workflow.add_edge("chat", END)
   
   
    resumeGo  = workflow.compile()
    return await resumeGo.ainvoke(AppState(user_input=user_input))
    
if __name__ == "__main__":
    import asyncio
    output = asyncio.run(ResumeGoRun("Give a rating of my resume as NYU supersmart student and intern at nvidia before for software engineer. Also, I have 3 AI robotic labs experiences."))
    #I used this fixed input for demo, it will later on be the AppState(check state.py) object that load the pdf from our frontend website
    print(output['result'])


# to run this on your terminal: 
# pipenv shell
# pipenv run python appRun.py