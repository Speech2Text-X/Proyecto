from psycopg_pool import ConnectionPool
import os

raw = os.getenv("DB_URL", "postgresql://postgres:postgres@localhost:5432/s2x")
DB_URL = raw.replace("postgresql+psycopg://", "postgresql://").replace("postgres+psycopg://", "postgres://")

pool = ConnectionPool(conninfo=DB_URL, min_size=1, max_size=10, kwargs={"autocommit": False})

def get_conn():
    return pool.connection()