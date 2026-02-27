from mongo import initMongo, closeMongo, getDatabase, getCollectionUsers, getCollectionSessions, getBucketResumes
from mongoUser import AddUserStatus, AddUserResult, LoginStatus, LoginResult, User
from mongoUser import addUser, login, validateUserLoginSession, getUserById, getUserByEmail
from mongoSession import SessionStatus, SessionInput, SessionOutput, Session
from mongoSession import createSession, getSessionById, getMostRecentSessionByUserId, getAllSessionsByUser, getAllSessionsByUserInStatus, completeSession, setSessionError, getFileBytesById



def runTests():
    # add user: happy path
    result = addUser("email@nyu.edu", "password", "my title", "my company", "my role", "my notes")
    assert result["status"] == AddUserStatus.SUCCESS

    user_id = result["user_id"]
    
    # add user: already exists
    result = addUser("email@nyu.edu", "password")
    assert result["status"] == AddUserStatus.ERROR_EMAIL_EXISTS_ALREADY

    # get user by id: bad id
    user = getUserById("blah")
    assert user == None
    
    # get user by id: happy path
    user = getUserById(user_id)
    assert user != None
    assert user["user_id"] == user_id
    assert user["email"] == "email@nyu.edu"
    assert user["title"] == "my title"
    assert user["company"] == "my company"
    assert user["role"] == "my role"
    assert user["notes"] == "my notes"

    # get user by email: bad email
    user = getUserByEmail("blah")
    assert user == None
    
    # get user by email: happy path (left out redundant asserts)
    user = getUserByEmail("email@nyu.edu")
    assert user != None
    assert user["user_id"] == user_id

    # login: existing username
    result = login("email@nyu.edu blah", "password")
    assert result["status"] == LoginStatus.ERROR_EMAIL_NOT_FOUND

    # login: incorrect password
    result = login("email@nyu.edu", "password blah")
    assert result["status"] == LoginStatus.ERROR_PASSWORD_INCORRECT

    # login: happy path
    result = login("email@nyu.edu", "password")
    assert result["status"] == LoginStatus.SUCCESS
    assert result["user_id"] == user_id

    login_session_id = result["login_session_id"]
    
    # validate: bad user id
    result = validateUserLoginSession("blah", "blah")
    assert not result

    # validate: bad login session id
    result = validateUserLoginSession(user_id, "blah")
    assert not result

    # validate: happy path
    result = validateUserLoginSession(user_id, login_session_id)
    assert result

    # super big brain session testing below...

    session1_id = createSession(user_id, "my job description 1", "my resume file name 1", bytes([1, 2, 3, 4]), "application/pdf", "my notes 1")
    session2_id = createSession(user_id, "my job description 2", "my resume file name 2", bytes([5, 6, 7, 8]), "application/pdf", "my notes 2")

    session = getSessionById("blah")
    assert session == None

    session = getSessionById(session1_id)
    assert session != None
    assert session["session_id"] == session1_id
    assert session["user_id"] == user_id
    assert session["status"] == SessionStatus.PENDING
    assert session["input"]["job_description"] == "my job description 1"
    assert session["input"]["resume_file_name"] == "my resume file name 1"
    assert session["input"]["resume_file_type"] == "application/pdf"
    assert session["input"]["notes"] == "my notes 1"
    assert session["output"] == None
    assert getFileBytesById(session["input"]["resume_file_id"]) == bytes([1, 2, 3, 4])

    session = getSessionById(session2_id)
    assert session != None
    assert session["session_id"] == session2_id
    assert session["user_id"] == user_id
    assert session["status"] == SessionStatus.PENDING
    assert session["input"]["job_description"] == "my job description 2"
    assert session["input"]["resume_file_name"] == "my resume file name 2"
    assert session["input"]["resume_file_type"] == "application/pdf"
    assert session["input"]["notes"] == "my notes 2"
    assert session["output"] == None
    assert getFileBytesById(session["input"]["resume_file_id"]) == bytes([5, 6, 7, 8])

    session = getMostRecentSessionByUserId(user_id)
    assert session["session_id"] == session2_id

    sessions = getAllSessionsByUser(user_id)
    assert len(sessions) == 2
    assert sessions[0]["session_id"] == session2_id
    assert sessions[1]["session_id"] == session1_id

    sessions = getAllSessionsByUserInStatus(user_id, SessionStatus.PENDING)
    assert len(sessions) == 2
    assert sessions[0]["session_id"] == session2_id
    assert sessions[1]["session_id"] == session1_id

    sessions = getAllSessionsByUserInStatus(user_id, SessionStatus.COMPLETE)
    assert len(sessions) == 0

    sessions = getAllSessionsByUserInStatus(user_id, SessionStatus.ERROR)
    assert len(sessions) == 0

    result = completeSession(session1_id, 100, ["1", "2"], ["3", "4"], ["5", "6"], ["7", "8"])
    assert result

    sessions = getAllSessionsByUserInStatus(user_id, SessionStatus.PENDING)
    assert len(sessions) == 1
    assert sessions[0]["session_id"] == session2_id

    sessions = getAllSessionsByUserInStatus(user_id, SessionStatus.COMPLETE)
    assert len(sessions) == 1
    assert sessions[0]["session_id"] == session1_id
    assert sessions[0]["output"]["match_score"] == 100
    assert sessions[0]["output"]["strong_matches"] == ["1", "2"]
    assert sessions[0]["output"]["missing_skills"] == ["3", "4"]
    assert sessions[0]["output"]["suggested_edits"] == ["5", "6"]
    assert sessions[0]["output"]["ai_insights"] == ["7", "8"]

    sessions = getAllSessionsByUserInStatus(user_id, SessionStatus.ERROR)
    assert len(sessions) == 0

    result = setSessionError(session2_id, "oops i did it again")
    assert result

    sessions = getAllSessionsByUserInStatus(user_id, SessionStatus.PENDING)
    assert len(sessions) == 0

    sessions = getAllSessionsByUserInStatus(user_id, SessionStatus.COMPLETE)
    assert len(sessions) == 1
    assert sessions[0]["session_id"] == session1_id

    sessions = getAllSessionsByUserInStatus(user_id, SessionStatus.ERROR)
    assert len(sessions) == 1
    assert sessions[0]["session_id"] == session2_id
    assert sessions[0]["error_msg"] == "oops i did it again"



DB_URI = "mongodb://localhost:27017/"
DB_NAME = "test"

from pymongo import MongoClient
client = MongoClient(DB_URI)
client.drop_database(DB_NAME)
client.close()

initMongo(DB_URI, DB_NAME)
runTests()
print("all tests passed!")
closeMongo()
