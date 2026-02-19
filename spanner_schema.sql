-- Create Tables
CREATE TABLE products (
    id INT64 NOT NULL,
    cost FLOAT64,
    category STRING(MAX),
    name STRING(MAX),
    brand STRING(MAX),
    retail_price FLOAT64,
    department STRING(MAX),
    sku STRING(MAX),
    distribution_center_id INT64,
    embedding ARRAY<FLOAT64>(vector_length=>768),
    product_description STRING(MAX),
    product_image_uri STRING(MAX),
    created_at TIMESTAMP,
    name_tokens TOKENLIST AS (TOKENIZE_FULLTEXT(name)) HIDDEN,
    category_tokens TOKENLIST AS (TOKENIZE_FULLTEXT(category)) HIDDEN,
    brand_tokens TOKENLIST AS (TOKENIZE_FULLTEXT(brand)) HIDDEN,
    description_tokens TOKENLIST AS (TOKENIZE_FULLTEXT(product_description)) HIDDEN,
) PRIMARY KEY (id);

CREATE TABLE users (
    id INT64 NOT NULL,
    first_name STRING(MAX),
    last_name STRING(MAX),
    email STRING(MAX),
    age INT64,
    gender STRING(MAX),
    state STRING(MAX),
    country STRING(MAX),
    city STRING(MAX),
) PRIMARY KEY (id);

CREATE TABLE orders (
    order_id INT64 NOT NULL,
    user_id INT64,
    status STRING(MAX),
    created_at TIMESTAMP,
) PRIMARY KEY (order_id);

CREATE TABLE order_items (
    id INT64 NOT NULL,
    order_id INT64,
    user_id INT64,
    product_id INT64,
    status STRING(MAX),
    sale_price FLOAT64,
) PRIMARY KEY (id);

CREATE INDEX OrderItemsByProduct ON order_items(product_id) STORING (user_id);
CREATE INDEX OrderItemsByUser ON order_items(user_id) STORING (product_id);

-- Search Index for Full-Text Search
CREATE SEARCH INDEX ProductsFTS ON products(name_tokens, category_tokens, brand_tokens, description_tokens);

-- Vector Index (Approximate Nearest Neighbor)
CREATE VECTOR INDEX ProductsVectorIndex ON products(embedding)
STORING (name, product_description, retail_price, product_image_uri)
WHERE embedding IS NOT NULL
OPTIONS (distance_type='COSINE');

-- Graph Definition for Recommendations
CREATE PROPERTY GRAPH RetailGraph
  NODE TABLES (
    products,
    users
  )
  EDGE TABLES (
    order_items AS purchased
      SOURCE KEY (user_id) REFERENCES users (id)
      DESTINATION KEY (product_id) REFERENCES products (id)
      LABEL purchased
  );
