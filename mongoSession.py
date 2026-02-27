from mongo import getCollectionSessions, getBucketResumes
from gridfs.errors import NoFile

from datetime import datetime
from zoneinfo import ZoneInfo
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
    notes: str

class SessionOutput(TypedDict):
    completed_at: datetime
    match_score: int
    strong_matches: list[str]
    missing_skills: list[str]
    suggested_edits: list[str]
    ai_insights: list[str]

class Session(TypedDict):
    session_id: str
    user_id: str
    status: SessionStatus
    error_msg: str | None
    input: SessionInput
    output: SessionOutput | None

def createSession(user_id: str, job_description: str, resume_file_name, resume_file_bytes: bytes, resume_file_type: str = "application/pdf", notes: str = "") -> str:
    session_id = str(uuid.uuid4())

    resume_file_id = getBucketResumes().upload_from_stream(
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
        "status": SessionStatus.PENDING.name,
        "error_msg": None,
        "input": {
            "requested_at": datetime.now(ZoneInfo("America/New_York")),
            "job_description": job_description,
            "resume_file_name": resume_file_name,
            "resume_file_id": resume_file_id,
            "resume_file_type": resume_file_type,
            "notes": notes
        },
        "output": None
    }

    getCollectionSessions().insert_one(session)
    return session_id

def _castToSession(session: dict) -> Session | None:
    status = session["status"]
    match status:
        case "PENDING":
            session["status"] = SessionStatus.PENDING
        case "COMPLETE":
            session["status"] = SessionStatus.COMPLETE
        case "ERROR":
            session["status"] = SessionStatus.ERROR
        case _:
            return None
    
    return cast(Session, session)

def _castToSessionList(sessions: list[dict]) -> list[Session]:
    sessions_new = []
    for s in sessions:
        session = _castToSession(s)
        if(session is not None):
            sessions_new.append(session)
    return sessions_new

def getSessionById(session_id: str) -> Session | None:
    result = getCollectionSessions().find_one({"session_id": session_id})
    if(result is None):
        return None
    return _castToSession(result)

def getMostRecentSessionByUserId(user_id: str) -> Session | None:
    result = getCollectionSessions().find_one({"user_id": user_id}, sort=[("input.requested_at", -1)])
    if(result is None):
        return None
    return _castToSession(result)

def getAllSessionsByUser(user_id: str) -> list[Session]:
    results = list(getCollectionSessions().find({"user_id": user_id}).sort("input.requested_at", -1))
    return _castToSessionList(results)

def getAllSessionsByUserInStatus(user_id: str, status: SessionStatus) -> list[Session]:
    results = list(getCollectionSessions().find({"user_id": user_id, "status": status.name}).sort("input.requested_at", -1))
    return _castToSessionList(results)

def completeSession(session_id: str, match_score: int, strong_matches: list[str], missing_skills: list[str], suggested_edits: list[str], ai_insights: list[str]) -> bool:
    result = getCollectionSessions().update_one(
        {"session_id": session_id},
        {"$set": {
            "status": SessionStatus.COMPLETE.name,
            "output": {
                "completed_at": datetime.now(ZoneInfo("America/New_York")),
                "match_score": match_score,
                "strong_matches": strong_matches,
                "missing_skills": missing_skills,
                "suggested_edits": suggested_edits,
                "ai_insights": ai_insights
            }
        }}
    )

    return result.modified_count == 1

def setSessionError(session_id: str, error_msg: str) -> bool:
    result = getCollectionSessions().update_one(
        {"session_id": session_id},
        {"$set": {
            "status": SessionStatus.ERROR.name,
            "error_msg": error_msg
        }}
    )

    return result.modified_count == 1

def getFileBytesById(file_id: ObjectId) -> bytes | None:
    buffer = io.BytesIO()

    try:
        getBucketResumes().download_to_stream(ObjectId(file_id), buffer)
    except NoFile:
        return None

    return buffer.getvalue()
