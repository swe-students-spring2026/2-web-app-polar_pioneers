from myllm import GetLLM
# from request_prompt import FILTER_PROMPT | will work on prompt engineering soon
from langchain_core.prompts import ChatPromptTemplate
import asyncio
from state import AppState

class ResumeAgent(GetLLM):

    def __init__(self, prompt, user_input:str):
        super().__init__(prompt=prompt)
        self.llm = self.get_llm()
        self.user_input = user_input

    async def run(self, state: AppState):
        
        prompt_template = ChatPromptTemplate.from_messages([
    ('system', self.prompt),
    ('human', "{user_request}")
    ])

        chain = prompt_template | self.llm
        state.user_input = self.user_input
    
        # formatted_prompt = prompt.format(user_request=UserInput)
    
        answer = await chain.ainvoke({"user_request": state.user_input})

        state.result = answer.content

        return state 

    async def __call__(self, state):
        return await self.run(state)
    
    # ResumeAgent("How is this resume?")

