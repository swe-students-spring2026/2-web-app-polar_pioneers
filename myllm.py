from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()


# this base LLM class will help me to set up my agent model

class GetLLM:
    """
    A class to get an instance of the LLM based on the provider(OpenAI for me).
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

    def get_openai_instance(self): # I use openai but you can feel free to use others 
        """Get an instance of the OpenAI LLM."""
        return ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.0,
            api_key=os.getenv("OPENAI_API_KEY") # remember to put your apikey in the .env
        )
    