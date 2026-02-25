import pymongo
import gridfs
from bson import ObjectId
client=pymongo.MongoClient("mongodb://localhost:27017/")
db = client["pdf_db"]
gridObject=gridfs.GridFS(db)
fileHandle=open("file_id.txt","r")
file_id=fileHandle.read()
resume_file=gridObject.get(file_id)
data=resume_file.read()
fileHandle.close()

