from flask import Blueprint, request, jsonify, render_template, current_app
from bson import ObjectId
from datetime import datetime, timezone

products_bp = Blueprint("products", __name__)

def get_db():
    return current_app.config["db"]

def fix_id(doc):
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

def parse_id(product_id):
    """Return _id as ObjectId if valid, else as string (ASIN)."""
    try:
        return ObjectId(product_id)
    except Exception:
        return product_id


# ── PAGE ───────────────────────────────────────────────────────────────────────
@products_bp.route("/")
def index():
    return render_template("products/index.html")


# ── API: list products ─────────────────────────────────────────────────────────
@products_bp.route("/api", methods=["GET"])
def api_list():
    db    = get_db()
    limit = int(request.args.get("limit", 20))
    asin  = request.args.get("asin")
    query = {}
    if asin:
        query["_id"] = {"$regex": asin, "$options": "i"}
    docs = list(db.products.find(query).limit(limit))
    return jsonify([fix_id(d) for d in docs])


# ── API: GET single ────────────────────────────────────────────────────────────
@products_bp.route("/api/<product_id>", methods=["GET"])
def api_get(product_id):
    db  = get_db()
    doc = db.products.find_one({"_id": parse_id(product_id)})
    if not doc:
        return jsonify({"error": "Not found"}), 404
    return jsonify(fix_id(doc))


# ── API: CREATE ────────────────────────────────────────────────────────────────
@products_bp.route("/api", methods=["POST"])
def api_create():
    db   = get_db()
    data = request.json or {}
    if "asin" not in data:
        return jsonify({"error": "Missing: asin"}), 400
    result = db.products.insert_one(data)
    return jsonify({"inserted_id": str(result.inserted_id)}), 201


# ── API: UPDATE ────────────────────────────────────────────────────────────────
@products_bp.route("/api/<product_id>", methods=["PUT"])
def api_update(product_id):
    db   = get_db()
    data = request.json or {}
    data.pop("_id", None)

    style_value = data.get("style")
    update_data = {"updatedAt": datetime.now(timezone.utc).isoformat()}
    if style_value:
        update_data["style"] = {"Style:": style_value} if isinstance(style_value, str) else style_value

    result = db.products.update_one({"_id": parse_id(product_id)}, {"$set": update_data})
    if result.matched_count == 0:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"modified": result.modified_count})


# ── API: DELETE ────────────────────────────────────────────────────────────────
@products_bp.route("/api/<product_id>", methods=["DELETE"])
def api_delete(product_id):
    db     = get_db()
    result = db.products.delete_one({"_id": parse_id(product_id)})
    if result.deleted_count == 0:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"deleted": result.deleted_count})


# ── API: product stats (aggregation) ──────────────────────────────────────────
@products_bp.route("/api/<asin>/stats", methods=["GET"])
def api_stats(asin):
    db = get_db()
    pipeline = [
        {"$match": {"asin": asin, "deleted_at": {"$exists": False}}},
        {"$group": {
            "_id": "$asin",
            "review_count": {"$sum": 1},
            "avg_rating":   {"$avg": "$overall"},
            "min_rating":   {"$min": "$overall"},
            "max_rating":   {"$max": "$overall"},
            "total_votes":  {"$sum": "$vote"},
            "verified_count": {"$sum": {"$cond": ["$verified", 1, 0]}}
        }}
    ]
    result = list(db.reviews.aggregate(pipeline))
    return jsonify(result[0] if result else {})