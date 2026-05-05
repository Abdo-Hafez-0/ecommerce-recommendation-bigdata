# Amazon Reviews Big Data Project

## Dataset Overview

This project is based on the Amazon Reviews dataset, where each record represents a single review event. A user (identified by `reviewerID`) reviews a product (identified by `asin`) and provides rating, feedback, and metadata.

The dataset is used to build a MongoDB-based system that supports querying, analytics, and sentiment analysis.

The original dataset contains millions of records (approximately 4 million), but during development, a sampled subset is used to improve performance and simplify testing.

---

## Dataset Structure

The dataset contains the following columns:

- overall  
- vote  
- verified  
- reviewTime  
- reviewerID  
- asin  
- style  
- reviewerName  
- reviewText  
- summary  
- unixReviewTime  

Each row represents a review linking a user to a product.

---

## Column Description

| Column Name     | Data Type   | Description |
|----------------|------------|-------------|
| overall        | float      | Rating given by the user (1 to 5) |
| vote           | int/string | Number of helpful votes |
| verified       | boolean    | Indicates whether the purchase is verified |
| reviewTime     | string     | Human-readable review date |
| reviewerID     | string     | Unique identifier for the user |
| asin           | string     | Unique identifier for the product |
| style          | object     | Product attributes (e.g., format, color) |
| reviewerName   | string     | Name of the reviewer |
| reviewText     | string     | Full review text |
| summary        | string     | Short summary of the review |
| unixReviewTime | int        | Review timestamp |

---

## Dataset Size

- Original dataset size: approximately 4 million records  
- Development subset: 20,000 to 50,000 records  
- Number of columns: 11  

To meet project requirements, additional derived fields will be introduced later (e.g., sentiment, review length), ensuring at least 12 meaningful attributes.

---


## Data Preprocessing

Before inserting the dataset into MongoDB, several preprocessing steps are applied:

1. Handling missing values:
   - Replace null values in text fields with empty strings  
   - Replace missing votes with 0  
   - Replace missing style with empty objects  

2. Data type conversion:
   - Convert vote to integer  
   - Convert overall to float  
   - Convert verified to boolean  

3. Duplicate removal:
   - Remove duplicate reviews based on reviewerID, asin, and timestamp  

4. Data consistency:
   - Ensure all fields follow a consistent structure  

These steps ensure clean and reliable data for storage and querying.

---

## Data Transformation for MongoDB

The dataset is transformed into multiple MongoDB collections based on its structure and relationships.

### Users Collection

Each unique user is stored as a document:

- `_id`: reviewerID  
- `name`: reviewerName  
- `profile` (embedded):
  - `total_reviews`  
  - `avg_rating`  

Relationship:
- One-to-Many: A user can write multiple reviews  

---

### Products Collection

Each product is stored as a document:

- `_id`: asin  
- `style`: product attributes  

Relationship:
- One-to-Many: A product can have multiple reviews  

---

### Reviews Collection

Each review is stored as a document:

- `reviewerID` (reference to user)  
- `asin` (reference to product)  
- `overall`  
- `vote`  
- `verified`  
- `reviewText`  
- `summary`  
- `reviewTime`  
- `unixReviewTime`  

Relationship:
- Many-to-Many: Users and products are connected through reviews  

---

## Relationships Summary

- One-to-Many:
  - User → Reviews  
  - Product → Reviews  

- Many-to-Many:
  - Users ↔ Products via Reviews  

- One-to-One:
  - User → Profile (embedded document)  

This design ensures efficient querying and aligns with MongoDB best practices.

---

## Summary

The dataset has been prepared, cleaned, and transformed into a structured format suitable for MongoDB. A subset is used during development, while the full dataset can be processed later for scalability testing.

This completes the dataset preparation and satisfies the first requirement of the project.

---

## Dataset Source and License

### Source

The dataset used in this project is the Amazon Reviews dataset, which is publicly available for research and educational purposes.

You can access the dataset from the following source:

- https://nijianmo.github.io/amazon/index.html  

---

### License

The Amazon Reviews dataset is typically distributed for academic and research use. It may fall under one of the following:

- Public dataset for non-commercial use  
- Research/educational purposes only  