import pymongo
from gridfs import GridFSBucket
from gridfs.errors import NoFile

from datetime import datetime
import uuid
import io

from enum import Enum
from typing import TypedDict
from typing import cast

from bson.objectid import ObjectId

class SessionStatus(Enum):
    PENDING = 0
    COMPLETE = 1
    ERROR = 2

class SessionInput(TypedDict):
    requested_at: datetime
    job_description: str
    resume_file_name: str
    resume_file_id: ObjectId
    resume_file_type: str

class SessionOutput(TypedDict):
    completed_at: datetime
    missing_skills: list[str] # TODO: may change type later
    strongest_matches: list[str] # TODO: may change type later
    suggested_edits: list[str] # TODO: may change type later

class Session(TypedDict):
    session_id: str
    user_id: str
    status: SessionStatus
    error_msg: str | None
    input: SessionInput
    output: SessionOutput | None

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["pdf_db"]
sessions = db["sessions"]

fs = GridFSBucket(db, bucket_name="resumes")

sessions.create_index("session_id", unique=True)
sessions.create_index([("user_id", 1), ("input.requested_at", -1)])
sessions.create_index([("user_id", 1), ("status", 1), ("input.requested_at", -1)])
sessions.create_index("input.resume_file_id")

def createSession(user_id: str, job_description: str, resume_file_name, resume_file_bytes: bytes, resume_file_type: str = "application/pdf") -> str:
    session_id = str(uuid.uuid4())

    resume_file_id = fs.upload_from_stream(
        resume_file_name,
        resume_file_bytes,
        metadata = {
            "user_id": user_id,
            "session_id": session_id,
            "content_type": resume_file_type
        }
    )

    session = {
        "session_id": session_id,
        "user_id": user_id,
        "status": SessionStatus.PENDING,
        "error_msg": None,
        "input": {
            "requested_at": datetime.now(datetime.timezone.utc),
            "job_description": job_description,
            "resume_file_name": resume_file_name,
            "resume_file_id": resume_file_id,
            "resume_file_type": resume_file_type
        },
        "output": None
    }

    sessions.insert_one(session)
    return session_id

def getSessionById(session_id: str) -> Session | None:
    result = sessions.find_one({"session_id": session_id})
    if(result is None):
        return None
    return cast(Session, result)

def getMostRecentSessionByUserId(user_id: str) -> Session | None:
    result = sessions.find_one({"user_id": user_id}, sort=[("input.requested_at", -1)])
    if(result is None):
        return None
    return cast(Session, result)

def getAllSessionsByStatus(user_id: str, status: SessionStatus) -> list[Session]:
    results = list(sessions.find({"user_id": user_id, "status": status}).sort("input.requested_at", -1))
    return cast(list[Session], results)

def completeSession(session_id: str, missing_skills, strongest_matches, suggested_edits) -> bool:
    result = sessions.update_one(
        {"session_id": session_id},
        {"$set": {
            "status": SessionStatus.COMPLETE,
            "output": {
                "completed_at": datetime.now(datetime.timezone.utc),
                "missing_skills": missing_skills,
                "strongest_matches": strongest_matches,
                "suggested_edits": suggested_edits
            }
        }}
    )

    return result.modified_count == 1

def setSessionError(session_id: str, error_msg: str) -> bool:
    result = sessions.update_one(
        {"session_id": session_id},
        {"$set": {
            "status": SessionStatus.ERROR,
            "error_msg": error_msg
        }}
    )

    return result.modified_count == 1

def getFileBytesById(file_id) -> bytes | None:
    buffer = io.BytesIO()

    try:
        fs.download_to_stream(ObjectId(file_id), buffer)
    except NoFile:
        return None

    return buffer.getvalue()
