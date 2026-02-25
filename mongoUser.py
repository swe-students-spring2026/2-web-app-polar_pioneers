import pymongo

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["pdf_db"]
users = db["users"]

from datetime import datetime
import uuid
import bcrypt

def hashPassword(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def addUser(username, password, name_first, name_last, email):
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

    users.insert_one(user)
