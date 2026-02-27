from langchain_core.runnables import Runnable
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Optional, Annotated
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

import os

load_dotenv()


# this base LLM class will be call from all the NODES to use 

class GetLLM:
    """
    A class to get an instance of the LLM based on the provider.
    """
    
    def __init__(self, provider ="openai", prompt = None):
        self.provider = provider
        self.prompt = prompt

    def get_llm(self):
        if self.provider == 'openai':
            llm = self.get_openai_instance()
        else:
            print("No llm model found")

        return llm

    def get_openai_instance(self):
        """Get an instance of the OpenAI LLM."""
        return ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.0,
            api_key=os.getenv("OPENAI_API_KEY")
        )
    