from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from gridfs import GridFSBucket

INITIALIZED: bool = False

client: MongoClient | None = None
db: Database | None = None
resumes: GridFSBucket | None = None

def initMongo(db_uri, db_name):
    global INITIALIZED, client, db, resumes

    if(INITIALIZED): return

    client = MongoClient(db_uri)
    db = client[db_name]

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

    INITIALIZED = True

def closeMongo():
    if(not INITIALIZED): raise RuntimeError("mongo not initialized")
    client.close()

def getDatabase() -> Database:
    if(not INITIALIZED): raise RuntimeError("mongo not initialized")
    return db

def getCollectionUsers() -> Collection:
    if(not INITIALIZED): raise RuntimeError("mongo not initialized")
    return db["users"]

def getCollectionSessions() -> Collection:
    if(not INITIALIZED): raise RuntimeError("mongo not initialized")
    return db["sessions"]

def getBucketResumes() -> GridFSBucket:
    if(not INITIALIZED): raise RuntimeError("mongo not initialized")
    return resumes
