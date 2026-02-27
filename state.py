from pydantic import BaseModel, Field
from typing import Optional

class AppState(BaseModel):
    """
    State model for the AI ResumeGo system.
    """

    user_input: str
    """ This is the query input from the user to ask question about our AI resume grading/consultant service, 
    it can be a scanned pdf of their resume, a question or a request for information related to the the resume , job market, personal info for applicants, etc"""
    job_description: str
    """"""
    resume_file_name:str
    """"""
    notes:str
    """"""
    result: str | None = None
    """ This is the result from the client node, it will be the answer to the user input query. """

   






