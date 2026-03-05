from myllm import GetLLM
# from request_prompt import FILTER_PROMPT | will work on prompt engineering soon
from langchain_core.prompts import ChatPromptTemplate #need it to make my request into langchain model redable ones
from state import AppState 

class ResumeAgent(GetLLM):# inherited from myllm.py where I set up the model

    def __init__(self, prompt: str, state:AppState):
        super().__init__(prompt=prompt)
        self.llm = self.get_llm() 

    async def run(self, state: AppState):
        
        prompt_template = ChatPromptTemplate.from_messages([
            ('system', self.prompt), #the system prompt here is higher priority that the agent should follow and I defined on appRun.
            ('human', 
                "Analyze the resume for this candidate specially about role he/she wants to apply for based on these info provided, and give an result/rating categorized in:\n"
                "1) Match Score (0-100)\n"
                "2) Strong Matches (bullet list)\n"
                "3) Missing Skills (bullet list)\n"
                "4) Suggested Edits (bullet list)\n"
                "5) AI Insights (paragraph)\n\n"
                "Uploaded resume filename: {resume_file_name}\n"
                "User notes: {notes}\n"
                "Job description:\n{job_description}\n\n"
                "Extracted resume text:\n{user_request}\n\n"
                "PDF bytes metadata: {pdf_bytes_info}"
            ) #human prompt here is the task request I want the agent to do. broke into details and formating.
        ])

        chain = prompt_template | self.llm #I pipe the prompt into the LLM to create an executable LangChain pipeline. output of left -> right basically


      


        answer = await chain.ainvoke(
            {
                "user_request": state.user_input, # this is the content on resume
                "resume_file_name": state.resume_file_name, #just keep the file name for reference, not going to weight analysis
                "notes": state.notes, #user's personal notes regarding to the analysis 
                "job_description": state.job_description, # the job that the user is going to analyze
                "pdf_bytes_info": state.resume_pdf_bytes, #the original bytes of the file for backup, storing in the database. 
            }
        )

        state.result = answer.content # I store the output of agent on result withing agentState. On Flask frontend, we will use output['result'] to get it since the agent return a dictionary type.

        return state 

    async def __call__(self, state):
        return await self.run(state)
    
    # ResumeAgent("How is this resume?") example question for agent

