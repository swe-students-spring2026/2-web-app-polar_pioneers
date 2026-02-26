from pydantic import BaseModel, Field
from typing import Optional

class AppState(BaseModel):
    """
    State model for the AI ResumeGo system.
    """

    user_input: str
    """ This is the query input from the user to ask question about our AI resume grading/consultant service, 
    it can be a scanned pdf of their resume, a question or a request for information related to the the resume , job market, personal info for applicants, etc"""
    result: Optional[str] = None
    """ This is the result from the client node, it will be the answer to the user input query. """


    output_checker: Optional[str] = None
    """ This is the result from the output checker node, it will be either 'yes'
    or 'no' based on whether the result correctly answered the user input query. """

    tryout: Optional[int] = None

    maxtry: Optional[int] = Field(default=5, description="Maximum number of attempts allowed for the user to get a valid response.")


