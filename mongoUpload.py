import pymongo
import gridfs
client=pymongo.MongoClient("mongodb://localhost:27017/")
db = client["pdf_db"]
gridObject = gridfs.GridFS(db)
fileHandle=open("resume.pdf","rb")
file_id=gridObject.put(fileHandle,filename="resume.pdf")
fileHandle.close()
fileHandle2=open("file_id.txt","w")
fileHandle2.write(file_id)
fileHandle2.close()


