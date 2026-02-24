from myllm import GetLLM
from request_prompt import FILTER_PROMPT 
from langchain_core.prompts import ChatPromptTemplate
import asyncio
from state import AppState

class MailRoomChatBot(GetLLM):

    def __init__(self, prompt, user_input:str):
        super().__init__(prompt=prompt)
        self.llm = self.get_llm()
        self.user_input = user_input

    async def run(self, state: AppState):
        # llm = LlmBase()
        # answer = llm.ainvoke({UserInput})
        # return answer 
        # llm = LlmBase()
        prompt_template = ChatPromptTemplate.from_messages([
    ('system', self.prompt),
    ('human', "{user_request}")
    ])

        chain = prompt_template | self.llm

        # user_input = input("Hi I'm your Mailbot, how can I help you today?\n User Query: ")
       
        state.user_input = self.user_input
    
        # formatted_prompt = prompt.format(user_request=UserInput)
    
        answer = await chain.ainvoke({"user_request": state.user_input})

        #use y/n for condition checking 
        # while(answer.content == "Sorry I can only answer questions related to the mailroom information."):
        #     user_input = input("Sorry I can only answer questions related to the mailroom information. Please ask again.\n User Query: ")
        #     answer = await chain.ainvoke({"user_request": user_input})
        # print(answer.content)
        return state 

    async def __call__(self, state):
        return await self.run(state)
    
    # mailbot("How many big packages does the mailroom have")

