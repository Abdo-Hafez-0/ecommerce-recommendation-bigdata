from flask import Blueprint, request, jsonify, render_template, current_app
from bson import ObjectId
from datetime import datetime, timezone

reviews_bp = Blueprint("reviews", __name__)

def get_db():
    return current_app.config["db"]

def fix_id(doc):
    """Convert ObjectId to string so jsonify works."""
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


# ── PAGE: list + search ────────────────────────────────────────────────────────
@reviews_bp.route("/")
def index():
    return render_template("reviews/index.html")


# ── API: GET all reviews (with optional filters) ───────────────────────────────
@reviews_bp.route("/api", methods=["GET"])
def api_list():
    db = get_db()
    query = {}

    asin       = request.args.get("asin")
    reviewer   = request.args.get("reviewerID")
    overall    = request.args.get("overall")
    verified   = request.args.get("verified")
    search     = request.args.get("search")
    limit      = int(request.args.get("limit", 20))

    if asin:       query["asin"]       = asin
    if reviewer:   query["reviewerID"] = reviewer
    if overall:    query["overall"]    = float(overall)
    if verified is not None:
        query["verified"] = (verified.lower() == "true")
    if search:
        query["$text"] = {"$search": search}

    # exclude soft-deleted
    query["deleted_at"] = {"$exists": False}

    docs = list(db.reviews.find(query).sort("unixReviewTime", -1).limit(limit))
    return jsonify([fix_id(d) for d in docs])


# ── API: GET single review ─────────────────────────────────────────────────────
@reviews_bp.route("/api/<review_id>", methods=["GET"])
def api_get(review_id):
    db = get_db()
    doc = db.reviews.find_one({"_id": ObjectId(review_id)})
    if not doc:
        return jsonify({"error": "Not found"}), 404
    return jsonify(fix_id(doc))


# ── API: CREATE review ─────────────────────────────────────────────────────────
@reviews_bp.route("/api", methods=["POST"])
def api_create():
    db = get_db()
    data = request.json or {}
    required = ["reviewerID", "asin", "overall", "reviewText", "summary"]
    missing  = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    data["verified"]       = data.get("verified", False)
    data["unixReviewTime"] = int(datetime.now(timezone.utc).timestamp())
    data["reviewTime"]     = datetime.now(timezone.utc).strftime("%m %d, %Y")

    result = db.reviews.insert_one(data)
    return jsonify({"inserted_id": str(result.inserted_id)}), 201


# ── API: UPDATE review ─────────────────────────────────────────────────────────
@reviews_bp.route("/api/<review_id>", methods=["PUT"])
def api_update(review_id):
    db = get_db()
    data = request.json or {}
    data.pop("_id", None)          # never update _id
    data["updatedAt"] = datetime.now(timezone.utc).isoformat()

    result = db.reviews.update_one(
        {"_id": ObjectId(review_id)},
        {"$set": data}
    )
    if result.matched_count == 0:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"modified": result.modified_count})


# ── API: SOFT DELETE ───────────────────────────────────────────────────────────
@reviews_bp.route("/api/<review_id>/soft", methods=["DELETE"])
def api_soft_delete(review_id):
    db = get_db()
    result = db.reviews.update_one(
        {"_id": ObjectId(review_id), "deleted_at": {"$exists": False}},
        {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}}
    )
    return jsonify({"modified": result.modified_count})


# ── API: HARD DELETE ───────────────────────────────────────────────────────────
@reviews_bp.route("/api/<review_id>", methods=["DELETE"])
def api_hard_delete(review_id):
    db = get_db()
    result = db.reviews.delete_one({"_id": ObjectId(review_id)})
    if result.deleted_count == 0:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"deleted": result.deleted_count})


# ── API: RESTORE soft-deleted ──────────────────────────────────────────────────
@reviews_bp.route("/api/<review_id>/restore", methods=["PATCH"])
def api_restore(review_id):
    db = get_db()
    result = db.reviews.update_one(
        {"_id": ObjectId(review_id)},
        {"$unset": {"deleted_at": ""}}
    )
    return jsonify({"modified": result.modified_count})