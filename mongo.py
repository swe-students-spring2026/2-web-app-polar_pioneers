from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from gridfs import GridFSBucket

client = MongoClient("mongodb://localhost:27017/")
db = client["pdf_db"]

users = db["users"]
users.create_index("user_id", unique=True)
users.create_index("username", unique=True)
users.create_index("email", unique=True)

sessions = db["sessions"]
sessions.create_index("session_id", unique=True)
sessions.create_index([("user_id", 1), ("input.requested_at", -1)])
sessions.create_index([("user_id", 1), ("status", 1), ("input.requested_at", -1)])
sessions.create_index("input.resume_file_id")

resumes = GridFSBucket(db, bucket_name="resumes")

def getDatabase() -> Database:
    return db

def getCollectionUsers() -> Collection:
    return users

def getCollectionSessions() -> Collection:
    return sessions

def getBucketResumes() -> GridFSBucket:
    return resumes
