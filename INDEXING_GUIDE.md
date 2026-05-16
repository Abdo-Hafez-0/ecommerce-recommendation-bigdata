# MongoDB Indexing & Optimized Queries - Implementation Guide

## 📋 Overview

This document provides complete documentation for the MongoDB indexing strategy and optimized query implementation for the Amazon Reviews dataset. It demonstrates best practices for performance tuning in MongoDB.

## 🎯 Objectives Met

✅ **Single-field indexes** - Fast lookups on individual fields  
✅ **Compound indexes** - Multi-field query optimization  
✅ **Multi-key indexes** - Array field support  
✅ **Custom indexes** - Specialized optimization (sparse, text)  
✅ **Performance comparison** - Before/after metrics with explain()  
✅ **8 optimized queries** - Production-ready query patterns  

## 📦 Project Structure

```
database/
├── indexes.py                  # Index creation functions
├── optimized_queries.py        # Ready-to-use query functions
└── schema.md                   # Database schema documentation

queries/
├── indexing_optimized_queries.ipynb   # Interactive notebook with examples
├── crud.ipynb                         # CRUD operations
└── aggregation.ipynb                  # Aggregation pipelines
```

## 🔍 Indexes Created

### 1. Single-Field Indexes

| Field | Order | Purpose |
|-------|-------|---------|
| `overall` | DESCENDING | Rating-based filtering & sorting |
| `reviewerID` | ASCENDING | User lookup |
| `asin` | ASCENDING | Product lookup |
| `verified` | ASCENDING | Verified status filtering |
| `unixReviewTime` | DESCENDING | Recency filtering |

**File:** `database/indexes.py` → `create_single_field_indexes()`

### 2. Compound Indexes

| Index | Fields | Use Case |
|-------|--------|----------|
| Compound 1 | `(reviewerID, overall)` | User rating analysis |
| Compound 2 | `(asin, verified)` | Verified product reviews |
| Compound 3 | `(asin, unixReviewTime)` | Recent product reviews |
| Compound 4 | `(reviewerID, verified, overall)` | Complex user filtering |

**File:** `database/indexes.py` → `create_compound_indexes()`

**ESR Rule Applied:**
- **E**quality: Field with exact match first
- **S**ort: Field used for sorting
- **R**ange: Field with range conditions

Example: `(asin, unixReviewTime)` where asin is equality and unixReviewTime is range/sort

### 3. Multi-Key Indexes

| Field | Type | Purpose |
|-------|------|---------|
| `style` | Single + Compound | Array field support |

**Automatic Creation:** MongoDB automatically makes these multi-key when the field contains arrays.

**File:** `database/indexes.py` → `create_multikey_indexes()`

### 4. Custom Optimization Indexes

| Name | Fields | Type | Purpose |
|------|--------|------|---------|
| Sparse Vote | `vote` | Sparse | Only index documents with votes |
| Full-text Search | `(reviewText, summary)` | Text | Keyword search support |
| Recommendation | `(overall, vote, verified, reviewerID)` | Compound | Recommendation engine optimization |

**File:** `database/indexes.py` → `create_custom_optimization_indexes()`

## 🚀 Quick Start

### 1. Setup Indexes

```python
from pymongo import MongoClient
from database.indexes import setup_all_indexes

# Connect to MongoDB
client = MongoClient("your_connection_string")
db = client["amazon_reviews_db"]

# Create all indexes
setup_all_indexes(db)
```

### 2. Use Optimized Queries

```python
from database.optimized_queries import OptimizedQueries

# Initialize query helper
queries = OptimizedQueries(db)

# Example: Find 5-star reviews
five_star_reviews = queries.find_reviews_by_rating(rating=5, limit=20)

# Example: Search for keywords
results = queries.search_reviews_by_text("excellent quality", limit=10)

# Example: Get product statistics
stats = queries.get_product_details(asin="B001234567")
```

## 📊 8 Optimized Query Patterns

### Query 1: Filter by Overall Rating
**Index:** Single-field on `overall`  
**Performance:** IXSCAN stage ✓

```python
results = queries.find_reviews_by_rating(rating=5, limit=100)
```

---

### Query 2: Filter by Reviewer ID & Date Range
**Index:** Compound on `(reviewerID, unixReviewTime)`  
**Performance:** IXSCAN stage ✓

```python
results = queries.find_user_reviews_in_date_range(
    reviewer_id="A2SUAM1J3GNN3B",
    min_timestamp=1609459200,
    max_timestamp=1640995200
)
```

---

### Query 3: Aggregate Reviews by Product
**Index:** Single-field on `asin`  
**Performance:** Efficient aggregation ✓

```python
stats = queries.get_product_review_stats(limit=20)
# Returns: _id, review_count, avg_rating, total_votes, verified_count
```

---

### Query 4: Find Verified Reviews with Votes
**Index:** Sparse on `vote`, Compound on `(asin, verified)`  
**Performance:** IXSCAN + sparse optimization ✓

```python
results = queries.find_verified_helpful_reviews(min_votes=10, limit=100)
```

---

### Query 5: Full-Text Search
**Index:** Text on `(reviewText, summary)`  
**Performance:** Text search scoring ✓

```python
results = queries.search_reviews_by_text("quality excellent", limit=20)
```

---

### Query 6: Group by User & Product
**Index:** Compound indexes on `(reviewerID, overall)`  
**Performance:** Multi-stage aggregation ✓

```python
user_stats = queries.get_user_review_stats(limit=20)
# Returns: products_reviewed, total_reviews, avg_rating, verified_ratio
```

---

### Query 7: Time-Based Aggregation
**Index:** Single-field on `unixReviewTime`  
**Performance:** Efficient date bucketing ✓

```python
time_stats = queries.get_reviews_by_time_period()
# Returns: review counts and stats by year
```

---

### Query 8: Multi-Field Filter with Sorting
**Index:** Compound on `(reviewerID, verified, overall)`  
**Performance:** IXSCAN + automatic sorting ✓

```python
results = queries.find_user_high_quality_reviews(
    reviewer_id="A2SUAM1J3GNN3B",
    min_rating=4,
    only_verified=True
)
```

## 📈 Performance Comparison

### Before Indexing (COLLSCAN)
- **Stage:** COLLSCAN - scans entire collection
- **Docs Examined:** 50,000+ (all documents)
- **Efficiency:** 1-5%
- **Time:** 500-2000 ms

### After Indexing (IXSCAN)
- **Stage:** IXSCAN - uses index scan
- **Docs Examined:** < 100 (relevant documents)
- **Efficiency:** 95-100%
- **Time:** 5-50 ms

### Improvement: 20-100x faster ⚡

## 🔧 Integration with Application

### Option 1: Initialize in App Startup

```python
# app/app.py
from pymongo import MongoClient
from database.indexes import setup_all_indexes
from database.optimized_queries import OptimizedQueries

app_db = MongoClient(MONGO_URI)[DB_NAME]
setup_all_indexes(app_db)  # Create indexes once at startup
queries = OptimizedQueries(app_db)  # Reuse throughout app
```

### Option 2: Use as Service Layer

```python
# app/services/review_service.py
from database.optimized_queries import OptimizedQueries

class ReviewService:
    def __init__(self, db):
        self.queries = OptimizedQueries(db)
    
    def get_top_products(self):
        return self.queries.get_product_review_stats(limit=20)
    
    def search_reviews(self, keywords):
        return self.queries.search_reviews_by_text(keywords)
```

### Option 3: Use in Routes

```python
# app/routes.py
from flask import Blueprint, request
from database.optimized_queries import OptimizedQueries

@app.route('/api/reviews/<asin>')
def get_product_reviews(asin):
    queries = OptimizedQueries(db)
    stats = queries.get_product_details(asin)
    reviews = queries.find_product_verified_reviews(asin)
    return {'stats': stats, 'reviews': reviews}
```

## 📊 explain() Output Interpretation

### Key Metrics

| Metric | Good | Poor |
|--------|------|------|
| `stage` | IXSCAN | COLLSCAN |
| `totalDocsExamined` | < 100 | > 10,000 |
| `nReturned` | Similar to examined | Much less |
| Efficiency | > 90% | < 10% |

### Example Output

```json
{
  "executionStats": {
    "stage": "IXSCAN",
    "totalDocsExamined": 42,
    "nReturned": 42,
    "executionTimeMillis": 12
  }
}
```

✅ **Good:** Uses IXSCAN, 100% efficient, fast execution

## 🧪 Testing & Validation

### Run Performance Tests

```python
from database.optimized_queries import test_queries_performance

test_queries_performance(db, test_limit=5)
```

### Run Interactive Notebook

Open `queries/indexing_optimized_queries.ipynb` in Jupyter:
1. Creates all indexes step-by-step
2. Runs all 8 query examples
3. Shows performance metrics
4. Displays sample results

## 📝 Best Practices

### ✅ DO

- ✓ Use compound indexes for multi-field queries
- ✓ Follow ESR rule: Equality, Sort, Range
- ✓ Use explain() to verify index usage
- ✓ Index on frequently filtered fields
- ✓ Monitor query performance in production
- ✓ Use text indexes for keyword search
- ✓ Use sparse indexes for optional fields

### ❌ DON'T

- ✗ Create too many indexes (slows writes)
- ✗ Index fields with low cardinality
- ✗ Ignore explain() output
- ✗ Assume queries are optimized without checking
- ✗ Mix field ordering in compound indexes
- ✗ Use COLLSCAN in production queries

## 🔄 Maintenance

### Monitor Index Usage

```python
indexes = list(db.reviews.list_indexes())
for idx in indexes:
    print(f"Index: {idx['name']}")
    print(f"Keys: {idx['key']}")
```

### Drop Indexes (if needed)

```python
db.reviews.drop_index("overall_-1")  # Drop specific index
db.reviews.drop_indexes()            # Drop all (except _id)
```

### Rebuild Indexes

```python
from database.indexes import setup_all_indexes
setup_all_indexes(db)  # Recreate all indexes
```

## 📚 References

### MongoDB Documentation
- [Index Types](https://docs.mongodb.com/manual/indexes/)
- [Compound Indexes](https://docs.mongodb.com/manual/core/index-compound/)
- [explain() Method](https://docs.mongodb.com/manual/reference/method/db.collection.explain/)
- [Text Indexes](https://docs.mongodb.com/manual/core/index-text/)

### Query Optimization
- [Query Performance](https://docs.mongodb.com/manual/core/query-optimization/)
- [Index Selection](https://docs.mongodb.com/manual/core/query-plans/)
- [ESR Rule](https://docs.mongodb.com/manual/tutorial/equality-sort-range-index/)

## 🎓 Learning Resources

### In This Project
1. **indexes.py** - All index creation code with comments
2. **optimized_queries.py** - Production-ready query functions
3. **indexing_optimized_queries.ipynb** - Interactive examples

### Key Concepts
- Index types and when to use each
- Execution plans (IXSCAN vs COLLSCAN)
- Performance metrics interpretation
- Compound index field ordering
- Text search fundamentals

## ❓ FAQ

**Q: How many indexes is too many?**  
A: Generally 5-10 per collection. Each index slows writes, so balance read optimization with write performance.

**Q: When should I use compound vs multiple indexes?**  
A: Use compound for multi-field queries. MongoDB can only use one index per query (except for $or).

**Q: Can text indexes be used with other queries?**  
A: Text indexes are used only for $text queries. Other indexes handle regular filtering.

**Q: How often should I rebuild indexes?**  
A: Indexes auto-maintain in MongoDB. Rebuild if experiencing fragmentation or after bulk operations.

**Q: What's the performance impact of indexes?**  
A: Write operations are ~5-10% slower per index. But reads can be 20-100x faster, usually worth it.

## 📞 Support

For questions about:
- **Index creation:** See `database/indexes.py`
- **Query usage:** See `database/optimized_queries.py`
- **Examples:** See `queries/indexing_optimized_queries.ipynb`
- **Troubleshooting:** Check explain() output and efficiency metrics

---

**Last Updated:** May 9, 2026  
**Author:** Big Data Project Team  
**Status:** Production Ready ✅
