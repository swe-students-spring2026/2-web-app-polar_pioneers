import pymongo
from pymongo.errors import DuplicateKeyError

from datetime import datetime
import uuid
import bcrypt

from enum import Enum
from typing import TypedDict
from typing import cast

class AddUserResult(Enum):
    SUCCESS = 0
    ERROR_UNKNOWN = 1
    ERROR_EXISTS_USERNAME = 2
    ERROR_EXISTS_EMAIL = 3

class Name(TypedDict):
    first: str
    last: str

class User(TypedDict):
    user_id: str
    username: str
    password_digest: str
    name: Name
    email: str
    date_joined: datetime

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["pdf_db"]
users = db["users"]

users.create_index("user_id", unique=True)
users.create_index("username", unique=True)
users.create_index("email", unique=True)

def hashPassword(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def addUser(username: str, password: str, name_first: str, name_last: str, email: str) -> AddUserResult:
    user = {
        "user_id": str(uuid.uuid4()),
        "username": username,
        "password_digest": hashPassword(password),
        "name": {
            "first": name_first,
            "last": name_last
        },
        "email": email,
        "date_joined": datetime.now(datetime.timezone.utc)
    }

    try:
        users.insert_one(user)
        return AddUserResult.SUCCESS
    except DuplicateKeyError as e:
        field = list(e.details["keyPattern"].keys())[0]
        match field:
            case "username":
                return AddUserResult.ERROR_EXISTS_USERNAME
            case "email":
                return AddUserResult.ERROR_EXISTS_EMAIL
            case _:
                return AddUserResult.ERROR_UNKNOWN

def getUserById(id: str) -> User | None:
    result = users.find_one({"user_id": id})
    if(result is None):
        return None
    return cast(User, result)

def getUserByUsername(username: str):
    result = users.find_one({"username": username})
    if(result is None):
        return None
    return cast(User, result)

def getUserByEmail(email: str):
    result = users.find_one({"email": email})
    if(result is None):
        return None
    return cast(User, result)
