from myllm import GetLLM
# from request_prompt import FILTER_PROMPT | will work on prompt engineering soon
from langchain_core.prompts import ChatPromptTemplate
from state import AppState

class ResumeAgent(GetLLM):

    def __init__(self, prompt: str):
        super().__init__(prompt=prompt)
        self.llm = self.get_llm()

    async def run(self, state: AppState):
        
        prompt_template = ChatPromptTemplate.from_messages([
            ('system', self.prompt),
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
            )
        ])

        chain = prompt_template | self.llm

        # Normalize and store defaults directly on state for consistent downstream usage.
        state.user_input = state.user_input or ""
        state.resume_file_name = state.resume_file_name or "Not provided"
        state.notes = state.notes or "None"
        state.job_description = state.job_description or "None"

        pdf_bytes_info = (
            f"present ({len(state.resume_pdf_bytes)} bytes)"
            if state.resume_pdf_bytes
            else "not provided"
        )

        answer = await chain.ainvoke(
            {
                "user_request": state.user_input,
                "resume_file_name": state.resume_file_name,
                "notes": state.notes,
                "job_description": state.job_description,
                "pdf_bytes_info": pdf_bytes_info,
            }
        )

        state.result = answer.content

        return state 

    async def __call__(self, state):
        return await self.run(state)
    
    # ResumeAgent("How is this resume?") example question for agent

