"""
MongoDB Optimized Query Examples & Testing
============================================

This module provides ready-to-use optimized query functions with performance testing.
Designed for easy integration into the main application.

Usage:
    from database.optimized_queries import OptimizedQueries
    
    # Initialize
    queries = OptimizedQueries(db)
    
    # Use optimized query functions
    results = queries.find_reviews_by_rating(rating=5)
    
Author: Big Data Project Team
"""

from pymongo import ASCENDING, DESCENDING
from typing import List, Dict, Any, Optional
import time


class OptimizedQueries:
    """Collection of optimized query methods for the Amazon Reviews dataset."""
    
    def __init__(self, db):
        """
        Initialize with database connection.
        
        Args:
            db: MongoDB database object
        """
        self.db = db
        self.reviews = db.reviews
        self.users = db.users
        self.products = db.products
    
    # ========================================================================
    # QUERY 1: Find Reviews by Overall Rating
    # ========================================================================
    
    def find_reviews_by_rating(self, rating: int, limit: int = 100) -> List[Dict]:
        """
        Find all reviews with a specific overall rating.
        
        Index Used: Single-field index on 'overall'
        
        Args:
            rating: Rating value (1-5)
            limit: Maximum number of results
        
        Returns:
            List of review documents
        
        Example:
            >>> queries.find_reviews_by_rating(rating=5, limit=20)
            [{'_id': ..., 'overall': 5, ...}, ...]
        """
        query = {"overall": rating}
        cursor = self.reviews.find(query).sort("unixReviewTime", -1).limit(limit)
        return list(cursor)
    
    def find_reviews_by_rating_range(self, min_rating: int, max_rating: int = 5, 
                                     limit: int = 100) -> List[Dict]:
        """
        Find reviews within a rating range.
        
        Args:
            min_rating: Minimum rating (inclusive)
            max_rating: Maximum rating (inclusive)
            limit: Maximum number of results
        
        Returns:
            List of review documents sorted by newest first
        """
        query = {"overall": {"$gte": min_rating, "$lte": max_rating}}
        cursor = self.reviews.find(query).sort("unixReviewTime", -1).limit(limit)
        return list(cursor)
    
    # ========================================================================
    # QUERY 2: Find Reviews by Reviewer ID and Date Range
    # ========================================================================
    
    def find_user_reviews_in_date_range(self, reviewer_id: str, 
                                        min_timestamp: int, 
                                        max_timestamp: int,
                                        limit: int = 100) -> List[Dict]:
        """
        Find all reviews from a specific user within a date range.
        
        Index Used: Compound index on (reviewerID, unixReviewTime)
        
        Args:
            reviewer_id: The reviewer's ID
            min_timestamp: Unix timestamp start (inclusive)
            max_timestamp: Unix timestamp end (inclusive)
            limit: Maximum number of results
        
        Returns:
            List of review documents
        
        Example:
            >>> queries.find_user_reviews_in_date_range(
            ...     reviewer_id="A2SUAM1J3GNN3B",
            ...     min_timestamp=1609459200,
            ...     max_timestamp=1640995200,
            ...     limit=50
            ... )
        """
        query = {
            "reviewerID": reviewer_id,
            "unixReviewTime": {
                "$gte": min_timestamp,
                "$lte": max_timestamp
            }
        }
        cursor = self.reviews.find(query).sort("unixReviewTime", -1).limit(limit)
        return list(cursor)
    
    # ========================================================================
    # QUERY 3: Aggregate Reviews by Product ASIN
    # ========================================================================
    
    def get_product_review_stats(self, limit: int = 20) -> List[Dict]:
        """
        Get review statistics aggregated by product ASIN.
        
        Index Used: Single-field index on 'asin'
        
        Args:
            limit: Number of top products to return
        
        Returns:
            List of documents with product stats
            
        Example output:
            {
                '_id': 'B001234567',
                'review_count': 150,
                'avg_rating': 4.2,
                'total_votes': 1250,
                'verified_count': 120
            }
        """
        pipeline = [
            {
                "$group": {
                    "_id": "$asin",
                    "review_count": {"$sum": 1},
                    "avg_rating": {"$avg": "$overall"},
                    "total_votes": {"$sum": "$vote"},
                    "verified_count": {
                        "$sum": {"$cond": ["$verified", 1, 0]}
                    }
                }
            },
            {"$sort": {"review_count": -1}},
            {"$limit": limit}
        ]
        return list(self.reviews.aggregate(pipeline))
    
    def get_product_details(self, asin: str) -> Dict:
        """
        Get detailed statistics for a specific product.
        
        Args:
            asin: Product ASIN
        
        Returns:
            Dictionary with product statistics
        """
        pipeline = [
            {"$match": {"asin": asin}},
            {
                "$group": {
                    "_id": "$asin",
                    "review_count": {"$sum": 1},
                    "avg_rating": {"$avg": "$overall"},
                    "min_rating": {"$min": "$overall"},
                    "max_rating": {"$max": "$overall"},
                    "total_votes": {"$sum": "$vote"},
                    "verified_count": {
                        "$sum": {"$cond": ["$verified", 1, 0]}
                    },
                    "latest_review_date": {"$max": "$unixReviewTime"}
                }
            }
        ]
        result = list(self.reviews.aggregate(pipeline))
        return result[0] if result else {}
    
    # ========================================================================
    # QUERY 4: Find Verified Reviews with High Votes
    # ========================================================================
    
    def find_verified_helpful_reviews(self, min_votes: int = 10, 
                                      limit: int = 100) -> List[Dict]:
        """
        Find verified reviews that have been marked as helpful (have votes).
        
        Index Used: Sparse index on 'vote', compound index on (asin, verified)
        
        Args:
            min_votes: Minimum helpful votes (default 10)
            limit: Maximum number of results
        
        Returns:
            List of verified helpful review documents
            
        Example:
            >>> queries.find_verified_helpful_reviews(min_votes=50, limit=20)
        """
        query = {
            "verified": True,
            "vote": {"$gte": min_votes}
        }
        cursor = (self.reviews
                 .find(query)
                 .sort("vote", -1)
                 .limit(limit))
        return list(cursor)
    
    def find_product_verified_reviews(self, asin: str, 
                                      limit: int = 50) -> List[Dict]:
        """
        Find all verified reviews for a specific product.
        
        Index Used: Compound index on (asin, verified)
        
        Args:
            asin: Product ASIN
            limit: Maximum number of results
        
        Returns:
            List of verified review documents for product
        """
        query = {
            "asin": asin,
            "verified": True
        }
        cursor = (self.reviews
                 .find(query)
                 .sort("unixReviewTime", -1)
                 .limit(limit))
        return list(cursor)
    
    # ========================================================================
    # QUERY 5: Full-Text Search on Review Content
    # ========================================================================
    
    def search_reviews_by_text(self, keywords: str, limit: int = 20) -> List[Dict]:
        """
        Search reviews by keywords in reviewText and summary.
        
        Index Used: Text index on (reviewText, summary)
        
        Args:
            keywords: Search keywords (supports AND, OR, negation)
            limit: Maximum number of results
        
        Returns:
            List of relevant review documents sorted by text relevance score
            
        Example:
            >>> queries.search_reviews_by_text("high quality product")
            >>> queries.search_reviews_by_text("excellent -expensive")  # Exclude word
        """
        query = {"$text": {"$search": keywords}}
        cursor = (self.reviews
                 .find(query, {"score": {"$meta": "textScore"}})
                 .sort([("score", {"$meta": "textScore"})])
                 .limit(limit))
        return list(cursor)
    
    # ========================================================================
    # QUERY 6: Group Reviews by User and Product
    # ========================================================================
    
    def get_user_review_stats(self, limit: int = 20) -> List[Dict]:
        """
        Get review statistics aggregated by reviewer.
        
        Index Used: Compound indexes on (reviewerID, overall)
        
        Args:
            limit: Number of top reviewers to return
        
        Returns:
            List of documents with user statistics
            
        Example output:
            {
                '_id': 'A2SUAM1J3GNN3B',
                'products_reviewed': 45,
                'total_reviews': 120,
                'avg_rating': 3.8,
                'verified_ratio': 0.85
            }
        """
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "reviewerID": "$reviewerID",
                        "asin": "$asin"
                    },
                    "review_count": {"$sum": 1},
                    "avg_rating": {"$avg": "$overall"},
                    "verified_reviews": {
                        "$sum": {"$cond": ["$verified", 1, 0]}
                    },
                    "total_votes": {"$sum": "$vote"}
                }
            },
            {
                "$group": {
                    "_id": "$_id.reviewerID",
                    "products_reviewed": {"$sum": 1},
                    "total_reviews": {"$sum": "$review_count"},
                    "avg_rating": {"$avg": "$avg_rating"},
                    "verified_ratio": {
                        "$avg": {
                            "$cond": [
                                {"$gt": ["$verified_reviews", 0]},
                                {"$divide": ["$verified_reviews", "$review_count"]},
                                0
                            ]
                        }
                    }
                }
            },
            {"$sort": {"total_reviews": -1}},
            {"$limit": limit}
        ]
        return list(self.reviews.aggregate(pipeline))
    
    def get_user_details(self, reviewer_id: str) -> Dict:
        """
        Get detailed statistics for a specific reviewer.
        
        Args:
            reviewer_id: The reviewer's ID
        
        Returns:
            Dictionary with user statistics
        """
        pipeline = [
            {"$match": {"reviewerID": reviewer_id}},
            {
                "$group": {
                    "_id": "$reviewerID",
                    "review_count": {"$sum": 1},
                    "avg_rating": {"$avg": "$overall"},
                    "verified_count": {
                        "$sum": {"$cond": ["$verified", 1, 0]}
                    },
                    "total_votes": {"$sum": "$vote"},
                    "products_reviewed": {"$addToSet": "$asin"}
                }
            },
            {
                "$addFields": {
                    "products_count": {"$size": "$products_reviewed"},
                    "verified_percentage": {
                        "$multiply": [
                            {"$divide": ["$verified_count", "$review_count"]},
                            100
                        ]
                    }
                }
            }
        ]
        result = list(self.reviews.aggregate(pipeline))
        return result[0] if result else {}
    
    # ========================================================================
    # QUERY 7: Time-Based Review Aggregation
    # ========================================================================
    
    def get_reviews_by_time_period(self) -> List[Dict]:
        """
        Get review counts aggregated by year from Unix timestamps.
        
        Index Used: Single-field index on 'unixReviewTime'
        
        Returns:
            List of documents with review counts per year
            
        Example output:
            {
                '_id': 1483228800,  # Unix timestamp for year start
                'review_count': 5000,
                'avg_rating': 3.8,
                'verified_count': 4200
            }
        """
        pipeline = [
            {
                "$bucket": {
                    "groupBy": "$unixReviewTime",
                    "boundaries": [
                        1483228800,  # 2017-01-01
                        1514764800,  # 2018-01-01
                        1546300800,  # 2019-01-01
                        1577836800,  # 2020-01-01
                        1609459200,  # 2021-01-01
                        1640995200   # 2022-01-01
                    ],
                    "default": "2022+",
                    "output": {
                        "review_count": {"$sum": 1},
                        "avg_rating": {"$avg": "$overall"},
                        "verified_count": {
                            "$sum": {"$cond": ["$verified", 1, 0]}
                        },
                        "total_votes": {"$sum": "$vote"}
                    }
                }
            }
        ]
        return list(self.reviews.aggregate(pipeline))
    
    def get_recent_reviews(self, days_back: int = 30, limit: int = 50) -> List[Dict]:
        """
        Get most recent reviews.
        
        Args:
            days_back: Number of days to look back
            limit: Maximum number of results
        
        Returns:
            List of recent review documents
        """
        # Calculate Unix timestamp for days_back
        import time
        cutoff_timestamp = int(time.time()) - (days_back * 86400)
        
        query = {"unixReviewTime": {"$gte": cutoff_timestamp}}
        cursor = (self.reviews
                 .find(query)
                 .sort("unixReviewTime", -1)
                 .limit(limit))
        return list(cursor)
    
    # ========================================================================
    # QUERY 8: Multi-Field Filter with Sorting
    # ========================================================================
    
    def find_user_high_quality_reviews(self, reviewer_id: str, 
                                       min_rating: int = 3,
                                       only_verified: bool = True,
                                       limit: int = 50) -> List[Dict]:
        """
        Find high-quality reviews from a specific user with optional verification filter.
        
        Index Used: Compound index on (reviewerID, verified, overall)
        
        Args:
            reviewer_id: The reviewer's ID
            min_rating: Minimum rating threshold
            only_verified: If True, only return verified reviews
            limit: Maximum number of results
        
        Returns:
            List of review documents sorted by newest first
            
        Example:
            >>> queries.find_user_high_quality_reviews(
            ...     reviewer_id="A2SUAM1J3GNN3B",
            ...     min_rating=4,
            ...     only_verified=True
            ... )
        """
        query = {
            "reviewerID": reviewer_id,
            "overall": {"$gte": min_rating}
        }
        
        if only_verified:
            query["verified"] = True
        
        cursor = (self.reviews
                 .find(query)
                 .sort("unixReviewTime", -1)
                 .limit(limit))
        return list(cursor)
    
    def find_recent_product_reviews(self, asin: str, 
                                    days_back: int = 90,
                                    min_rating: int = 1,
                                    limit: int = 50) -> List[Dict]:
        """
        Find recent reviews for a product within a date range.
        
        Index Used: Compound index on (asin, unixReviewTime)
        
        Args:
            asin: Product ASIN
            days_back: Number of days to look back
            min_rating: Minimum rating to include
            limit: Maximum number of results
        
        Returns:
            List of recent review documents
        """
        import time
        cutoff_timestamp = int(time.time()) - (days_back * 86400)
        
        query = {
            "asin": asin,
            "unixReviewTime": {"$gte": cutoff_timestamp},
            "overall": {"$gte": min_rating}
        }
        
        cursor = (self.reviews
                 .find(query)
                 .sort("unixReviewTime", -1)
                 .limit(limit))
        return list(cursor)
    
    # ========================================================================
    # PERFORMANCE ANALYSIS
    # ========================================================================
    
    def explain_query(self, query: Dict, collection_name: str = "reviews") -> Dict:
        """
        Get the execution plan for a query.
        
        Args:
            query: MongoDB query filter
            collection_name: Collection to query
        
        Returns:
            Full explain() output with execution statistics
        """
        collection = self.db[collection_name]
        return collection.find(query).explain()
    
    def analyze_query_performance(self, query: Dict, 
                                  collection_name: str = "reviews") -> Dict:
        """
        Analyze query performance and return key metrics.
        
        Args:
            query: MongoDB query filter
            collection_name: Collection to query
        
        Returns:
            Dictionary with performance metrics
        """
        collection = self.db[collection_name]
        
        start_time = time.time()
        cursor = collection.find(query)
        results = list(cursor)
        execution_time = time.time() - start_time
        
        explain_output = collection.find(query).explain()
        exec_stats = explain_output.get('executionStats', {})
        
        return {
            'results_count': len(results),
            'execution_time_ms': execution_time * 1000,
            'docs_examined': exec_stats.get('totalDocsExamined', 0),
            'docs_returned': exec_stats.get('nReturned', 0),
            'execution_stage': exec_stats.get('executionStages', {}).get('stage', 'UNKNOWN'),
            'index_used': 'IXSCAN' in exec_stats.get('executionStages', {}).get('stage', ''),
            'efficiency_percent': (
                exec_stats.get('nReturned', 1) / 
                max(exec_stats.get('totalDocsExamined', 1), 1) * 100
            )
        }


# ============================================================================
# HELPER FUNCTIONS FOR QUICK INTEGRATION
# ============================================================================

def create_all_indexes(db) -> None:
    """Create all recommended indexes for the project."""
    from database.indexes import setup_all_indexes
    setup_all_indexes(db)


def test_queries_performance(db, test_limit: int = 5) -> None:
    """
    Run a quick performance test on all query types.
    
    Args:
        db: MongoDB database object
        test_limit: Number of results per query for testing
    """
    queries = OptimizedQueries(db)
    
    print("\n" + "="*70)
    print("🧪 PERFORMANCE TEST SUITE")
    print("="*70)
    
    test_cases = [
        ("Rating Filter (5 stars)", {"overall": 5}),
        ("Verified High Votes", {"verified": True, "vote": {"$gte": 10}}),
        ("Recent Reviews", {"unixReviewTime": {"$gte": 1609459200}}),
    ]
    
    for test_name, query in test_cases:
        print(f"\n📊 {test_name}")
        metrics = queries.analyze_query_performance(query)
        
        print(f"   Time: {metrics['execution_time_ms']:.2f} ms")
        print(f"   Docs: {metrics['docs_examined']} examined, {metrics['docs_returned']} returned")
        print(f"   Stage: {metrics['execution_stage']}")
        print(f"   Efficiency: {metrics['efficiency_percent']:.1f}%")


if __name__ == "__main__":
    # Example usage
    from pymongo import MongoClient
    
    MONGO_URI = "mongodb+srv://abdohafez731_db_user:xQ4Nmj6FoicluMap@cluster0.p6b5wtu.mongodb.net/?retryWrites=true&w=majority"
    client = MongoClient(MONGO_URI)
    db = client["amazon_reviews_db"]
    
    queries = OptimizedQueries(db)
    
    # Run sample query
    print("Finding 5-star reviews...")
    results = queries.find_reviews_by_rating(rating=5, limit=5)
    print(f"Found {len(results)} reviews")
    
    # Test performance
    test_queries_performance(db)
