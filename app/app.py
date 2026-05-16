from flask import Flask
from pymongo import MongoClient
from pymongo.errors import PyMongoError

MONGO_URI = "mongodb+srv://abdohafez731_db_user:xQ4Nmj6FoicluMap@cluster0.p6b5wtu.mongodb.net/?retryWrites=true&w=majority"
DB_NAME = "amazon_reviews_db"

app = Flask(__name__)

# ── DB connection ──────────────────────────────────────────────────────────────
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
app.config["db"] = db

# ── Blueprints ─────────────────────────────────────────────────────────────────
from routes.reviews  import reviews_bp
from routes.users    import users_bp
from routes.products import products_bp
from routes.dashboard import dashboard_bp

app.register_blueprint(dashboard_bp)
app.register_blueprint(reviews_bp,  url_prefix="/reviews")
app.register_blueprint(users_bp,    url_prefix="/users")
app.register_blueprint(products_bp, url_prefix="/products")

if __name__ == "__main__":
    app.run(debug=True)