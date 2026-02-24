import pymongo
client=pymongo.MongoClient("mongodb://localhost:27017/")
db = client["pdf_db"]
gridObject = pymongo.gridfs.GridFS(db)
fileHandle=open("resume.pdf","rb")
gridObject.put(fileHandle,filename="resume.pdf")
fileHandle.close()

