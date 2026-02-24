import pymongo
import gridfs
from pathlib import Path
client=pymongo.MongoClient("mongodb://localhost:27017/")
db = client["pdf_db"]
gridObject = gridfs.GridFS(db)
fileHandle=open("resume.pdf","rb")
gridObject.put(fileHandle,filename="resume.pdf")
fileHandle.close()

