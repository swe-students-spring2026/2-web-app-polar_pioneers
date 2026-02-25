import pymongo
from pymongo.errors import DuplicateKeyError

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["pdf_db"]
users = db["users"]

users.create_index("user_id", unique=True)
users.create_index("username", unique=True)
users.create_index("email", unique=True)

from datetime import datetime
import uuid
import bcrypt

def hashPassword(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

from enum import Enum

class AddUserResult(Enum):
    SUCCESS = 0
    ERROR_UNKNOWN = 1
    ERROR_EXISTS_USERNAME = 2
    ERROR_EXISTS_EMAIL = 3

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

def getUserById(id):
    return users.find_one({"user_id": id})

def getUserByUsername(username):
    return users.find_one({"username": username})

def getUserByEmail(email):
    return users.find_one({"email": email})
