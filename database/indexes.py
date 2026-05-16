"""
MongoDB Indexing Strategy & Performance Optimization
======================================================

This module implements comprehensive indexing strategies for the Amazon Reviews dataset.
Includes single-field, compound, multi-key, and custom indexes with performance analysis.

Collections:
- users: User information with embedded profile
- products: Product details
- reviews: Review documents with all review fields

Author: Big Data Project Team
"""

from pymongo import MongoClient, ASCENDING, DESCENDING, GEOSPHERE
from pymongo.errors import PyMongoError, OperationFailure
import time
import pprint
from typing import Dict, List, Any, Tuple


# ============================================================================
# DATABASE CONNECTION
# ============================================================================

MONGO_URI = "mongodb+srv://abdohafez731_db_user:xQ4Nmj6FoicluMap@cluster0.p6b5wtu.mongodb.net/?retryWrites=true&w=majority"
DB_NAME = "amazon_reviews_db"


def get_db():
    """Initialize MongoDB connection and return database object."""
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        # Verify connection
        db.admin.command('ping')
        print("[✓] Connected to MongoDB Atlas")
        return db
    except PyMongoError as e:
        print(f"[✗] Connection Error: {e}")
        raise


# ============================================================================
# INDEX CREATION FUNCTIONS
# ============================================================================

def create_single_field_indexes(db) -> Dict[str, str]:
    """
    Create single-field indexes for frequently searched fields.
    
    Purpose:
    - Accelerate single field lookups
    - Common in filtering operations
    
    Returns:
        Dict with index names
    """
    print("\n" + "="*70)
    print("1️⃣  CREATING SINGLE-FIELD INDEXES")
    print("="*70)
    
    indexes_created = {}
    
    # Index on reviewerID for quick user lookup
    idx_name = db.reviews.create_index([("reviewerID", ASCENDING)])
    indexes_created["reviewerID"] = idx_name
    print(f"✓ Created index on 'reviewerID': {idx_name}")
    
    # Index on product ASIN for product lookups
    idx_name = db.reviews.create_index([("asin", ASCENDING)])
    indexes_created["asin"] = idx_name
    print(f"✓ Created index on 'asin': {idx_name}")
    
    # Index on overall rating for sorting
    idx_name = db.reviews.create_index([("overall", DESCENDING)])
    indexes_created["overall"] = idx_name
    print(f"✓ Created index on 'overall': {idx_name}")
    
    # Index on verified status for filtering
    idx_name = db.reviews.create_index([("verified", ASCENDING)])
    indexes_created["verified"] = idx_name
    print(f"✓ Created index on 'verified': {idx_name}")
    
    # Index on unixReviewTime for date-based queries
    idx_name = db.reviews.create_index([("unixReviewTime", DESCENDING)])
    indexes_created["unixReviewTime"] = idx_name
    print(f"✓ Created index on 'unixReviewTime': {idx_name}")
    
    return indexes_created


def create_compound_indexes(db) -> Dict[str, str]:
    """
    Create compound indexes for multi-field lookups.
    
    Purpose:
    - Optimize queries filtering on multiple fields
    - Support sorted results on field combinations
    - Follow ESR rule: Equality, Sort, Range
    
    Returns:
        Dict with compound index names
    """
    print("\n" + "="*70)
    print("2️⃣  CREATING COMPOUND INDEXES")
    print("="*70)
    
    indexes_created = {}
    
    # Compound index: reviewerID + overall (for user ratings analysis)
    # ESR Rule: reviewerID (equality), overall (sort/range)
    idx_name = db.reviews.create_index([
        ("reviewerID", ASCENDING),
        ("overall", DESCENDING)
    ])
    indexes_created["reviewerID_overall"] = idx_name
    print(f"✓ Compound index (reviewerID, overall): {idx_name}")
    
    # Compound index: asin + verified (for verified product reviews)
    # ESR Rule: asin (equality), verified (equality)
    idx_name = db.reviews.create_index([
        ("asin", ASCENDING),
        ("verified", ASCENDING)
    ])
    indexes_created["asin_verified"] = idx_name
    print(f"✓ Compound index (asin, verified): {idx_name}")
    
    # Compound index: asin + unixReviewTime (for recent reviews)
    # ESR Rule: asin (equality), unixReviewTime (sort)
    idx_name = db.reviews.create_index([
        ("asin", ASCENDING),
        ("unixReviewTime", DESCENDING)
    ])
    indexes_created["asin_unixReviewTime"] = idx_name
    print(f"✓ Compound index (asin, unixReviewTime): {idx_name}")
    
    # Compound index: reviewerID + verified + overall
    # For complex filtering on verified reviews by users with ratings
    idx_name = db.reviews.create_index([
        ("reviewerID", ASCENDING),
        ("verified", ASCENDING),
        ("overall", DESCENDING)
    ])
    indexes_created["reviewerID_verified_overall"] = idx_name
    print(f"✓ Compound index (reviewerID, verified, overall): {idx_name}")
    
    return indexes_created


def create_multikey_indexes(db) -> Dict[str, str]:
    """
    Create multi-key indexes for array field queries.
    
    Purpose:
    - Optimize queries on embedded/array fields
    - Automatically created when indexing array fields
    - Useful for searching within style variants
    
    Returns:
        Dict with multi-key index names
    """
    print("\n" + "="*70)
    print("3️⃣  CREATING MULTI-KEY INDEXES")
    print("="*70)
    
    indexes_created = {}
    
    # Multi-key index on style (if it contains array values)
    # Note: MongoDB automatically makes this a multi-key index if style is an array
    idx_name = db.reviews.create_index([("style", ASCENDING)])
    indexes_created["style"] = idx_name
    print(f"✓ Multi-key index on 'style': {idx_name}")
    
    # Compound multi-key index: asin + style
    # For searching products by ASIN with specific style variants
    idx_name = db.reviews.create_index([
        ("asin", ASCENDING),
        ("style", ASCENDING)
    ])
    indexes_created["asin_style"] = idx_name
    print(f"✓ Compound multi-key index (asin, style): {idx_name}")
    
    return indexes_created


def create_custom_optimization_indexes(db) -> Dict[str, str]:
    """
    Create custom indexes specifically optimized for recommendation engine.
    
    Purpose:
    - Support recommendation system queries
    - Optimize aggregation pipelines
    - Custom sparse indexes for specific use cases
    
    Returns:
        Dict with custom index names
    """
    print("\n" + "="*70)
    print("4️⃣  CREATING CUSTOM OPTIMIZATION INDEXES")
    print("="*70)
    
    indexes_created = {}
    
    # Sparse index on vote count (only documents with votes)
    # Optimizes filtering by verified votes
    idx_name = db.reviews.create_index(
        [("vote", DESCENDING)],
        sparse=True  # Only index documents with 'vote' field
    )
    indexes_created["vote_sparse"] = idx_name
    print(f"✓ Sparse index on 'vote': {idx_name}")
    
    # Text index on reviewText and summary for full-text search
    # Optimizes searching review content
    idx_name = db.reviews.create_index([
        ("reviewText", "text"),
        ("summary", "text")
    ])
    indexes_created["fulltext_search"] = idx_name
    print(f"✓ Text index (reviewText, summary): {idx_name}")
    
    # Compound index optimized for recommendation: 
    # overall + vote + verified + reviewerID
    # Sort by helpfulness (vote) and rating quality
    idx_name = db.reviews.create_index([
        ("overall", DESCENDING),
        ("vote", DESCENDING),
        ("verified", ASCENDING),
        ("reviewerID", ASCENDING)
    ])
    indexes_created["recommendation_score"] = idx_name
    print(f"✓ Recommendation optimization index: {idx_name}")
    
    # Index for user profile lookups (one-to-one relationship)
    idx_name = db.users.create_index([("_id", ASCENDING)])
    indexes_created["users_id"] = idx_name
    print(f"✓ Index on 'users._id': {idx_name}")
    
    return indexes_created


def list_all_indexes(db) -> None:
    """Display all existing indexes in collections."""
    print("\n" + "="*70)
    print("📋 ALL EXISTING INDEXES")
    print("="*70)
    
    for collection_name in db.list_collection_names():
        collection = db[collection_name]
        indexes = collection.list_indexes()
        print(f"\n Collection: '{collection_name}'")
        for idx in indexes:
            print(f"  - {idx['name']}: {idx['key']}")


def drop_all_indexes(db, exclude_id: bool = True) -> None:
    """
    Remove all indexes (except _id) for testing.
    
    Args:
        db: Database object
        exclude_id: If True, keep _id index (recommended)
    """
    print("\n" + "="*70)
    print("🗑️  DROPPING INDEXES")
    print("="*70)
    
    for collection_name in ["users", "products", "reviews"]:
        if collection_name in db.list_collection_names():
            collection = db[collection_name]
            try:
                if exclude_id:
                    # Drop all indexes except _id_
                    collection.drop_indexes()
                    # Re-create _id index if needed
                    print(f"✓ Dropped all indexes from '{collection_name}' (kept _id)")
                else:
                    collection.drop_indexes()
                    print(f"✓ Dropped all indexes from '{collection_name}'")
            except OperationFailure as e:
                print(f"[!] Could not drop indexes from {collection_name}: {e}")


# ============================================================================
# PERFORMANCE ANALYSIS FUNCTIONS
# ============================================================================

def run_query_with_timing(db, collection_name: str, query: Dict, 
                         explain: bool = False) -> Tuple[List[Dict], Dict, float]:
    """
    Execute a query with timing and explain plan.
    
    Args:
        db: Database object
        collection_name: Name of collection to query
        query: MongoDB query filter
        explain: Whether to show explain() output
    
    Returns:
        Tuple of (results, explain_plan, execution_time)
    """
    collection = db[collection_name]
    
    start_time = time.time()
    cursor = collection.find(query)
    results = list(cursor)
    execution_time = time.time() - start_time
    
    explain_plan = {}
    if explain:
        explain_plan = collection.find(query).explain()
    
    return results, explain_plan, execution_time


def performance_comparison(db, query: Dict, collection_name: str = "reviews") -> None:
    """
    Compare query performance before and after indexing.
    
    Args:
        db: Database object
        query: MongoDB query filter
        collection_name: Collection to query
    """
    collection = db[collection_name]
    
    print("\n" + "-"*70)
    print(f"Query: {query}")
    print("-"*70)
    
    # Execute query
    start_time = time.time()
    cursor = collection.find(query)
    results = list(cursor)
    execution_time = time.time() - start_time
    
    # Get explain plan
    explain_plan = collection.find(query).explain()
    
    # Extract relevant metrics
    execution_stats = explain_plan.get('executionStats', {})
    docs_examined = execution_stats.get('totalDocsExamined', 0)
    docs_returned = execution_stats.get('nReturned', 0)
    
    print(f"Results: {len(results)} documents")
    print(f"Execution Time: {execution_time*1000:.2f} ms")
    print(f"Docs Examined: {docs_examined}")
    print(f"Docs Returned: {docs_returned}")
    print(f"Efficiency: {(docs_returned/docs_examined*100):.2f}%" if docs_examined > 0 else "N/A")
    print(f"\nExecution Stage: {execution_stats.get('executionStages', {}).get('stage', 'N/A')}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def setup_all_indexes(db) -> None:
    """Create all indexes for the project."""
    print("\n" + "█"*70)
    print("█  MONGODB INDEXING SETUP - AMAZON REVIEWS DATABASE")
    print("█"*70)
    
    create_single_field_indexes(db)
    create_compound_indexes(db)
    create_multikey_indexes(db)
    create_custom_optimization_indexes(db)
    
    print("\n" + "█"*70)
    print("█  INDEX SETUP COMPLETE")
    print("█"*70)
    
    list_all_indexes(db)


if __name__ == "__main__":
    db = get_db()
    setup_all_indexes(db)
