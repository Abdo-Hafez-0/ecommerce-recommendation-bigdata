from flask import Blueprint, request, jsonify, render_template, current_app
from datetime import datetime, timezone

users_bp = Blueprint("users", __name__)

def get_db():
    return current_app.config["db"]

def fix_id(doc):
    """_id في الـ users هو الـ reviewerID نفسه (string مش ObjectId)"""
    if doc and "_id" in doc:
        doc["reviewerID"] = str(doc["_id"])
        doc["_id"]        = str(doc["_id"])
    return doc


# ── PAGE ───────────────────────────────────────────────────────────────────────
@users_bp.route("/")
def index():
    return render_template("users/index.html")


# ── API: list users ────────────────────────────────────────────────────────────
@users_bp.route("/api", methods=["GET"])
def api_list():
    db    = get_db()
    limit = int(request.args.get("limit", 20))
    name  = request.args.get("name")
    query = {}
    if name:
        query["name"] = {"$regex": name, "$options": "i"}   # ✅ الـ field اسمه name
    docs = list(db.users.find(query).limit(limit))
    return jsonify([fix_id(d) for d in docs])


# ── API: GET single ────────────────────────────────────────────────────────────
@users_bp.route("/api/<user_id>", methods=["GET"])
def api_get(user_id):
    db  = get_db()
    # _id في users هو string مش ObjectId
    doc = db.users.find_one({"_id": user_id})
    if not doc:
        return jsonify({"error": "Not found"}), 404
    return jsonify(fix_id(doc))


# ── API: CREATE ────────────────────────────────────────────────────────────────
@users_bp.route("/api", methods=["POST"])
def api_create():
    db   = get_db()
    data = request.json or {}
    # نستخدم reviewerID كـ _id عشان يتطابق مع باقي الـ collections
    required = ["reviewerID", "name"]
    missing  = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing: {missing}"}), 400

    doc = {
        "_id" : data["reviewerID"],   # ✅ نفس نمط الـ collection
        "name": data["name"],
        "profile": data.get("profile", {})
    }
    try:
        result = db.users.insert_one(doc)
        return jsonify({"inserted_id": str(result.inserted_id)}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ── API: UPDATE ────────────────────────────────────────────────────────────────
@users_bp.route("/api/<user_id>", methods=["PUT"])
def api_update(user_id):
    db   = get_db()
    data = request.json or {}
    data.pop("_id", None)
    data.pop("reviewerID", None)
    result = db.users.update_one({"_id": user_id}, {"$set": data})
    if result.matched_count == 0:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"modified": result.modified_count})


# ── API: DELETE ────────────────────────────────────────────────────────────────
@users_bp.route("/api/<user_id>", methods=["DELETE"])
def api_delete(user_id):
    db     = get_db()
    result = db.users.delete_one({"_id": user_id})   
    if result.deleted_count == 0:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"deleted": result.deleted_count})


# ── API: user's reviews ────────────────────────────────────────────────────────
@users_bp.route("/api/<reviewer_id>/reviews", methods=["GET"])
def api_user_reviews(reviewer_id):
    db   = get_db()
    docs = list(db.reviews.find(
        {"reviewerID": reviewer_id, "deleted_at": {"$exists": False}}
    ).sort("unixReviewTime", -1).limit(50))
    return jsonify([fix_id(d) for d in docs])