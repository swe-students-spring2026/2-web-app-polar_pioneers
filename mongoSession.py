import pymongo
from gridfs import GridFSBucket

from datetime import datetime

from enum import Enum
from typing import TypedDict
from typing import cast

from bson.objectid import ObjectId

class SessionStatus(Enum):
    PENDING = 0
    FINISHED = 1
    ERROR = 2

class SessionInput(TypedDict):
    requested_at: datetime
    resume_file_name: str
    resume_file_id: ObjectId
    job_description: str

class SessionOutput(TypedDict):
    completed_at: datetime
    missing_skills: list[str] # TODO: may change type later
    strongest_matches: list[str] # TODO: may change type later
    suggested_edits: list[str] # TODO: may change type later

class Session(TypedDict):
    session_id: str
    user_id: str
    status: SessionStatus
    input: SessionInput
    output: SessionOutput | None

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["pdf_db"]
sessions = db["sessions"]

fs = GridFSBucket(db, bucket_name="resumes")

sessions.create_index("session_id", unique=True)
sessions.create_index([("user_id", 1), ("input.requested_at", -1)])
sessions.create_index("input.resume_file_id")

