import os
import sqlalchemy
from google.cloud.alloydb.connector import Connector, IPTypes
from google.cloud import spanner
import datetime
import json
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = "alloydbtest-374215"
REGION = "us-central1"
# AlloyDB
ALLOYDB_CLUSTER = "hybridsearch"
ALLOYDB_INSTANCE = "hybridsearch-primary"
ALLOYDB_DB = "ecom"
ALLOYDB_USER = "postgres"
ALLOYDB_PASS = "Qbertq!1"
ALLOYDB_CONNECTION_NAME = f"projects/{PROJECT_ID}/locations/{REGION}/clusters/{ALLOYDB_CLUSTER}/instances/{ALLOYDB_INSTANCE}"
# Spanner
SPANNER_INSTANCE_ID = "virtual-retail-instance"
SPANNER_DATABASE_ID = "catalog"

def get_alloydb_connection():
    """Establishes a connection to AlloyDB."""
    connector = Connector()
    def getconn():
        conn = connector.connect(
            ALLOYDB_CONNECTION_NAME,
            "pg8000",
            user=ALLOYDB_USER,
            password=ALLOYDB_PASS,
            db=ALLOYDB_DB,
            ip_type=IPTypes.PUBLIC, # Using Public IP as we are outside VPC
        )
        return conn
    
    pool = sqlalchemy.create_engine(
        "postgresql+pg8000://",
        creator=getconn,
    )
    return pool

def get_spanner_database():
    """Establishes a connection to Spanner."""
    spanner_client = spanner.Client(project=PROJECT_ID)
    instance = spanner_client.instance(SPANNER_INSTANCE_ID)
    database = instance.database(SPANNER_DATABASE_ID)
    return database

def parse_embedding(embedding_str):
    """Parses pgvector string representation to list of floats."""
    if isinstance(embedding_str, list):
        return embedding_str
    if isinstance(embedding_str, str):
        # Format usually '[0.1,0.2,...]'
        return json.loads(embedding_str)
    return None

def migrate_products(alloy_conn, spanner_db):
    logger.info("Migrating Products...")
    with alloy_conn.connect() as conn:
        # Fetch products
        # Note: Adjust columns based on actual schema
        query = sqlalchemy.text("""
            SELECT id, cost, category, name, brand, retail_price, department, sku, 
                   distribution_center_id, embedding, product_description, product_image_uri 
            FROM products
        """)
        result = conn.execute(query)
        
        batch_size = 500
        rows = []
        
        def insert_batch(transaction, batch):
             transaction.insert_or_update(
                "products",
                columns=["id", "cost", "category", "name", "brand", "retail_price", "department", "sku", 
                         "distribution_center_id", "embedding", "product_description", "product_image_uri", "created_at"],
                values=batch
             )

        count = 0
        for row in result:
            # Transform row to Spanner format
            # Spanner expects specific types.
            # Embedding needs to be list of floats.
            try:
                emb = parse_embedding(row[9])
                
                # Construct row
                # Add created_at as now()
                spanner_row = (
                    row[0], # id
                    float(row[1]) if row[1] else None, # cost
                    row[2], # category
                    row[3], # name
                    row[4], # brand
                    float(row[5]) if row[5] else None, # retail_price
                    row[6], # department
                    row[7], # sku
                    row[8], # distribution_center_id
                    emb,    # embedding
                    row[10], # product_description
                    row[11], # product_image_uri
                    datetime.datetime.utcnow() # created_at
                )
                rows.append(spanner_row)
                count += 1
                
                if len(rows) >= batch_size:
                    spanner_db.run_in_transaction(insert_batch, batch=rows)
                    rows = []
                    logger.info(f"Migrated {count} products...")
            except Exception as e:
                logger.error(f"Error processing row {row[0]}: {e}")

        if rows:
            spanner_db.run_in_transaction(insert_batch, batch=rows)
            logger.info(f"Final batch. Total products migrated: {count}")

def migrate_users(alloy_conn, spanner_db):
    logger.info("Migrating Users...")
    with alloy_conn.connect() as conn:
        query = sqlalchemy.text("""
            SELECT id, first_name, last_name, email, age, gender, state, country, city
            FROM users
        """)
        result = conn.execute(query)
        
        batch_size = 1000
        rows = []
        
        def insert_batch(transaction, batch):
             transaction.insert_or_update(
                "users",
                columns=["id", "first_name", "last_name", "email", "age", "gender", "state", "country", "city"],
                values=batch
             )

        count = 0
        for row in result:
            rows.append(row)
            count += 1
            if len(rows) >= batch_size:
                spanner_db.run_in_transaction(insert_batch, batch=rows)
                rows = []
                logger.info(f"Migrated {count} users...")

        if rows:
            spanner_db.run_in_transaction(insert_batch, batch=rows)
            logger.info(f"Total users migrated: {count}")

def migrate_orders(alloy_conn, spanner_db):
    logger.info("Migrating Orders...")
    with alloy_conn.connect() as conn:
        query = sqlalchemy.text("SELECT order_id, user_id, status, created_at FROM orders")
        result = conn.execute(query)
        
        batch_size = 1000
        rows = []
        
        def insert_batch(transaction, batch):
             transaction.insert_or_update(
                "orders",
                columns=["order_id", "user_id", "status", "created_at"],
                values=batch
             )

        count = 0
        for row in result:
            rows.append(row)
            count += 1
            if len(rows) >= batch_size:
                spanner_db.run_in_transaction(insert_batch, batch=rows)
                rows = []

        if rows:
            spanner_db.run_in_transaction(insert_batch, batch=rows)
            logger.info(f"Total orders migrated: {count}")

def migrate_order_items(alloy_conn, spanner_db):
    logger.info("Migrating Order Items...")
    with alloy_conn.connect() as conn:
        query = sqlalchemy.text("SELECT id, order_id, user_id, product_id, status, sale_price FROM order_items")
        result = conn.execute(query)
        
        batch_size = 1000
        rows = []
        
        def insert_batch(transaction, batch):
             transaction.insert_or_update(
                "order_items",
                columns=["id", "order_id", "user_id", "product_id", "status", "sale_price"],
                values=batch
             )

        count = 0
        for row in result:
            # Need to cast sale_price to float if it's Decimal
            vals = list(row)
            if vals[5] is not None:
                vals[5] = float(vals[5])
            
            rows.append(tuple(vals))
            count += 1
            if len(rows) >= batch_size:
                spanner_db.run_in_transaction(insert_batch, batch=rows)
                rows = []

        if rows:
            spanner_db.run_in_transaction(insert_batch, batch=rows)
            logger.info(f"Total order items migrated: {count}")

def main():
    try:
        logger.info("Connecting to AlloyDB...")
        alloy_conn = get_alloydb_connection()
        
        logger.info("Connecting to Spanner...")
        spanner_db = get_spanner_database()
        
        # Verify AlloyDB Connection first
        with alloy_conn.connect() as conn:
             conn.execute(sqlalchemy.text("SELECT 1"))
        logger.info("AlloyDB Connection Verified.")

        # Migrate Tables
        migrate_users(alloy_conn, spanner_db)
        migrate_products(alloy_conn, spanner_db)
        migrate_orders(alloy_conn, spanner_db)
        migrate_order_items(alloy_conn, spanner_db)
        
        logger.info("Migration Completed Successfully!")
        
    except Exception as e:
        logger.error(f"Migration Failed: {e}")

if __name__ == "__main__":
    main()
