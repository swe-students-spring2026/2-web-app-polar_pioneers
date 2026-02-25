import pymongo

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["pdf_db"]
users = db["users"]

from datetime import datetime
import uuid

def addUser(username, password_digest, name_first, name_last, email):
    user = {
        "user_id": str(uuid.uuid4()),
        "username": username,
        "password_digest": password_digest,
        "name": {
            "first": name_first,
            "last": name_last
        },
        "email": email,
        "date_joined": datetime.now(datetime.timezone.utc)
    }

    users.insert_one(user)

# import gridfs
# gridObject = gridfs.GridFS(db)
# fileHandle=open("resume.pdf","rb")
# file_id=gridObject.put(fileHandle,filename="resume.pdf")
# fileHandle.close()
# fileHandle2=open("file_id.txt","w")
# fileHandle2.write(file_id)
# fileHandle2.close()


