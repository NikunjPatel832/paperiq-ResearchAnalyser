from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
import datetime

# -------------------------
# MongoDB Connection
# -------------------------
client = MongoClient("mongodb://localhost:27017/")
db = client["iq_project_db"]

users_collection = db["users"]
documents_collection = db["documents"]

# -------------------------
# User Management
# -------------------------
def register_user(username: str, password: str):
    """Register new user"""
    if users_collection.find_one({"username": username}):
        return False  # User already exists
    pw_hash = generate_password_hash(password)
    users_collection.insert_one({
        "username": username,
        "password_hash": pw_hash,
        "created_at": datetime.datetime.utcnow()
    })
    return True


def validate_user(username: str, password: str) -> bool:
    """Validate login"""
    user = users_collection.find_one({"username": username})
    if not user:
        return False
    return check_password_hash(user["password_hash"], password)


# -------------------------
# Document Handling
# -------------------------
def save_document(username: str, filename: str, filepath: str,
                  raw_text: str, preprocessed_text: str,
                  summary: str, insights: dict):
    """Save uploaded document details"""
    doc = {
        "username": username,
        "filename": filename,
        "filepath": filepath,
        "raw_text": raw_text,
        "preprocessed_text": preprocessed_text,
        "summary": summary,
        "insights": insights,
        "created_at": datetime.datetime.utcnow()
    }
    result = documents_collection.insert_one(doc)
    return str(result.inserted_id)


def get_user_documents(username: str):
    """Fetch user’s documents"""
    docs = []
    for d in documents_collection.find({"username": username}).sort("created_at", -1):
        created_at_value = d.get("created_at", "")
        # Safely convert datetime to string if needed
        if isinstance(created_at_value, datetime.datetime):
            created_at_value = created_at_value.isoformat()
        docs.append({
            "id": str(d["_id"]),
            "filename": d.get("filename"),
            "filepath": d.get("filepath"),
            "summary": d.get("summary"),
            "insights": d.get("insights", {}),
            "created_at": created_at_value
        })
    return docs


def get_document_by_id(doc_id):
    """Fetch document by ObjectId"""
    try:
        doc = documents_collection.find_one({"_id": ObjectId(doc_id)})
        if not doc:
            return None
        doc["id"] = str(doc["_id"])
        return doc
    except Exception as e:
        print(f"Error fetching document: {e}")
        return None


# -------------------------
# Analytics / Metrics
# -------------------------
def get_metrics_last_n_days(n=7):
    """Return upload counts and entity frequency"""
    today = datetime.date.today()

    # Upload counts
    counts = []
    for i in range(n - 1, -1, -1):
        day = today - datetime.timedelta(days=i)
        next_day = day + datetime.timedelta(days=1)
        count = documents_collection.count_documents({
            "created_at": {
                "$gte": datetime.datetime.combine(day, datetime.time.min),
                "$lt": datetime.datetime.combine(next_day, datetime.time.min)
            }
        })
        counts.append({"day": day.isoformat(), "count": count})

    # Entity frequency
    entity_counter = {}
    for doc in documents_collection.find({}, {"insights": 1}):
        insights = doc.get("insights", {})
        for ent in insights.get("entities", []):
            label = ent[1] if len(ent) > 1 else "UNKNOWN"
            entity_counter[label] = entity_counter.get(label, 0) + 1

    return counts, entity_counter
