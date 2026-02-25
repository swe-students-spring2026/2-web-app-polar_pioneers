"""
db.py - MongoDB connection and all database operations for ResumeGo
"""

import os
from datetime import datetime
from bson.objectid import ObjectId
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()  # loads variables from .env file

# --- Connection ---

def get_db():
    """Returns the ResumeGo database instance."""
    client = MongoClient(os.getenv("MONGO_URI"))
    return client[os.getenv("MONGO_DBNAME", "resumego")]


# --- User operations ---

def create_user(username, password_digest, first_name, last_name, email):
    """Insert a new user. Returns the inserted user's id."""
    db = get_db()
    user = {
        "username": username,
        "password_digest": password_digest,  # store bcrypt hash, never plaintext
        "name_first": first_name,
        "name_last": last_name,
        "email": email,
        "created_at": datetime.utcnow()
    }
    result = db.users.insert_one(user)
    return str(result.inserted_id)


def get_user_by_username(username):
    """Find a user by username. Returns user dict or None."""
    db = get_db()
    return db.users.find_one({"username": username})


def get_user_by_id(user_id):
    """Find a user by their ObjectId string."""
    db = get_db()
    return db.users.find_one({"_id": ObjectId(user_id)})


# --- Analysis (run) operations ---

def create_analysis(user_id, resume_text, job_description, score, missing_skills, strongest_matches, suggested_edits, job_title=""):
    """
    Save a new analysis to the database.
    Returns the inserted analysis id as a string.
    """
    db = get_db()
    analysis = {
        "user_id": user_id,           # links back to the user
        "job_title": job_title,        # optional, useful for searching
        "input": {
            "resume_text": resume_text,
            "job_description": job_description,
            "submitted_at": datetime.utcnow()
        },
        "output": {
            "score": score,                          # e.g. 82 (out of 100)
            "missing_skills": missing_skills,        # list of strings
            "strongest_matches": strongest_matches,  # list of strings
            "suggested_edits": suggested_edits,      # list of strings
            "completed_at": datetime.utcnow()
        }
    }
    result = db.analyses.insert_one(analysis)
    return str(result.inserted_id)


def get_analyses_by_user(user_id):
    """
    Get all analyses for a given user, sorted newest first.
    Returns a list of analysis dicts.
    """
    db = get_db()
    results = db.analyses.find({"user_id": user_id}).sort("input.submitted_at", -1)
    return list(results)


def get_analysis_by_id(analysis_id):
    """Get a single analysis by its id string."""
    db = get_db()
    return db.analyses.find_one({"_id": ObjectId(analysis_id)})


def update_analysis_job_description(analysis_id, new_job_description):
    """
    Edit the job description of a saved analysis.
    Returns True if something was updated, False otherwise.
    """
    db = get_db()
    result = db.analyses.update_one(
        {"_id": ObjectId(analysis_id)},
        {"$set": {
            "input.job_description": new_job_description,
            "input.edited_at": datetime.utcnow()
        }}
    )
    return result.modified_count > 0


def delete_analysis(analysis_id):
    """
    Delete an analysis by its id.
    Returns True if something was deleted, False otherwise.
    """
    db = get_db()
    result = db.analyses.delete_one({"_id": ObjectId(analysis_id)})
    return result.deleted_count > 0


def search_analyses(user_id, keyword):
    """
    Search a user's analyses by keyword in job_title or job_description.
    Returns a list of matching analysis dicts.
    """
    db = get_db()
    results = db.analyses.find({
        "user_id": user_id,
        "$or": [
            {"job_title": {"$regex": keyword, "$options": "i"}},
            {"input.job_description": {"$regex": keyword, "$options": "i"}}
        ]
    }).sort("input.submitted_at", -1)
    return list(results)