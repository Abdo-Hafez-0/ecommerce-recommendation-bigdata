from flask import Blueprint, render_template, jsonify, current_app

dashboard_bp = Blueprint("dashboard", __name__)

def get_db():
    return current_app.config["db"]


@dashboard_bp.route("/")
def index():
    return render_template("dashboard.html")


# ── API: summary stats ─────────────────────────────────────────────────────────
@dashboard_bp.route("/api/stats")
def api_stats():
    db = get_db()
    return jsonify({
        "total_reviews":  db.reviews.count_documents({"deleted_at": {"$exists": False}}),
        "total_users":    db.users.count_documents({}),
        "total_products": db.products.count_documents({}),
        "deleted_reviews": db.reviews.count_documents({"deleted_at": {"$exists": True}}),
    })


# ── API: top products ──────────────────────────────────────────────────────────
@dashboard_bp.route("/api/top-products")
def api_top_products():
    db = get_db()
    pipeline = [
        {"$match": {"deleted_at": {"$exists": False}}},
        {"$group": {
            "_id": "$asin",
            "review_count": {"$sum": 1},
            "avg_rating":   {"$avg": "$overall"}
        }},
        {"$match": {"review_count": {"$gte": 3}}},
        {"$sort": {"avg_rating": -1}},
        {"$limit": 10}
    ]
    return jsonify(list(db.reviews.aggregate(pipeline)))


# ── API: rating distribution ───────────────────────────────────────────────────
@dashboard_bp.route("/api/rating-dist")
def api_rating_dist():
    db = get_db()
    pipeline = [
        {"$match": {"deleted_at": {"$exists": False}}},
        {"$group": {"_id": "$overall", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    return jsonify(list(db.reviews.aggregate(pipeline)))


# ── API: verified vs unverified ────────────────────────────────────────────────
@dashboard_bp.route("/api/verified-stats")
def api_verified_stats():
    db = get_db()
    pipeline = [
        {"$match": {"deleted_at": {"$exists": False}}},
        {"$group": {
            "_id": "$verified",
            "count":      {"$sum": 1},
            "avg_rating": {"$avg": "$overall"}
        }}
    ]
    return jsonify(list(db.reviews.aggregate(pipeline)))


# ── API: reviews over time ─────────────────────────────────────────────────────
@dashboard_bp.route("/api/reviews-over-time")
def api_reviews_over_time():
    db = get_db()
    pipeline = [
        {"$match": {"deleted_at": {"$exists": False}}},
        {"$project": {
            "year_month": {
                "$dateToString": {
                    "format": "%Y-%m",
                    "date": {"$toDate": {"$multiply": ["$unixReviewTime", 1000]}}
                }
            }
        }},
        {"$group": {"_id": "$year_month", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
        {"$limit": 24}
    ]
    return jsonify(list(db.reviews.aggregate(pipeline)))