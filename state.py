from pydantic import BaseModel # needed to keep AppState validated and consistent across the workflow.

#State is going to be passed around the entire END TO END
class AppState(BaseModel):
    """
    State model for the AI ResumeGo system.
    """

    user_input: str
    """ This is the resume pdf input from the user to ask question about our AI resume agent grading/consultant service, 
    it can be a scanned pdf of their resume, a question or a request for information related to the the resume , job market, personal info for applicants, etc"""
    job_description:  str | None = None
    """This will be the job description of what the user wants to apply for and you have you include the the thinking in your analysis"""
    resume_file_name: str | None = None
    """this is just the file name of the resume on user_input, don't have to affect the analysis, just store it here"""
    resume_pdf_bytes: bytes | None = None
    """This is the raw pdf bytes for storage and reuse. Just in case."""
    notes: str | None = None
    """This can be any notes that the user personally wants you to consider in the resume consulting analysis."""
    result: str | None = None
    """ This is the result from the client node, it will be the answer to the user input query. """

   




