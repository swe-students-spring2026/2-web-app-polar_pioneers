from mongo import getCollectionUsers
from pymongo.errors import DuplicateKeyError

from datetime import datetime
import uuid
import bcrypt

from enum import Enum
from typing import TypedDict
from typing import cast

class AddUserStatus(Enum):
    SUCCESS = 0
    ERROR_UNKNOWN = 1
    ERROR_EXISTS_EMAIL = 2

class AddUserResult(TypedDict):
    status: AddUserStatus
    user_id: str | None # if status != SUCCESS, user_id = None

class User(TypedDict):
    user_id: str
    email: str
    password_digest: str
    title: str
    company: str
    role: str
    notes: str
    login_session_id: str

def hashPassword(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def addUser(email: str, password: str, title: str = "", company: str = "", role: str = "", notes: str = "") -> AddUserResult:
    user_id = str(uuid.uuid4())
    user = {
        "user_id": user_id,
        "email": email,
        "password_digest": hashPassword(password),
        "title": title,
        "company": company,
        "role": role,
        "notes": notes
    }

    try:
        getCollectionUsers().insert_one(user)
        return {"status": AddUserStatus.SUCCESS, "user_id": user_id}
    except DuplicateKeyError as e:
        field = list(e.details["keyPattern"].keys())[0]
        match field:
            case "email":
                return {"status": AddUserStatus.ERROR_EXISTS_EMAIL}
            case _:
                return {"status": AddUserStatus.ERROR_UNKNOWN}

def getUserById(user_id: str) -> User | None:
    result = getCollectionUsers().find_one({"user_id": user_id})
    if(result is None):
        return None
    return cast(User, result)

def getUserByEmail(email: str) -> User | None:
    result = getCollectionUsers().find_one({"email": email})
    if(result is None):
        return None
    return cast(User, result)

# TODO: setUserUsername
# TODO: setUserPassword
# TODO: setUserNameFirst
# TODO: setUserNameLast
# TODO: setUserEmail

# TODO: removeUser
