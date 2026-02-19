import os
from google.cloud.alloydb.connector import Connector, IPTypes
import sqlalchemy

# Configuration
PROJECT_ID = "alloydbtest-374215"
REGION = "us-central1"
CLUSTER = "hybridsearch"
INSTANCE = "hybridsearch-primary"
DATABASE = "ecom"
USER = "postgres"
PASSWORD = "Qbertq!1"
INSTANCE_CONNECTION_NAME = f"projects/{PROJECT_ID}/locations/{REGION}/clusters/{CLUSTER}/instances/{INSTANCE}"

def getconn():
    with Connector() as connector:
        conn = connector.connect(
            INSTANCE_CONNECTION_NAME,
            "pg8000",
            user=USER,
            password=PASSWORD,
            db=DATABASE,
            ip_type=IPTypes.PUBLIC,
        )
        return conn

def verify_connection():
    try:
        pool = sqlalchemy.create_engine(
            "postgresql+pg8000://",
            creator=getconn,
        )
        with pool.connect() as db_conn:
            result = db_conn.execute(sqlalchemy.text("SELECT version();")).fetchone()
            print(f"Connected successfully! Server version: {result[0]}")
            
            # Check for tables
            result = db_conn.execute(sqlalchemy.text("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';")).fetchone()
            print(f"Number of tables in public schema: {result[0]}")
            
            # List some tables
            result = db_conn.execute(sqlalchemy.text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' LIMIT 5;"))
            print("Tags found:")
            for row in result:
                print(f" - {row[0]}")

    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    verify_connection()
