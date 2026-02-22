"""
Database connection and utilities for Outpass Management System.
"""

import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager
import os
import sys

# Database configuration - use environment variables in production
DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "outpass_clean"),
    "autocommit": True,
}


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        yield conn
    except Error as e:
        error_msg = str(e)
        print(f"Database connection error: {e}")
        if "Access denied" in error_msg or "1698" in error_msg:
            print("\n" + "="*60)
            print("MySQL AUTHENTICATION ERROR")
            print("="*60)
            print("Possible solutions:")
            print("1. Set MySQL password via environment variable:")
            print("   export MYSQL_PASSWORD='your_mysql_password'")
            print("\n2. Or create a MySQL user with password:")
            print("   sudo mysql -e \"CREATE USER 'outpass_user'@'localhost' IDENTIFIED BY 'your_password';\"")
            print("   sudo mysql -e \"GRANT ALL ON outpass_clean.* TO 'outpass_user'@'localhost';\"")
            print("   Then set: export MYSQL_USER='outpass_user'")
            print("            export MYSQL_PASSWORD='your_password'")
            print("\n3. Or use sudo mysql to access root (if auth_socket):")
            print("   sudo mysql -u root")
            print("="*60)
        raise
    finally:
        if conn and conn.is_connected():
            conn.close()


def get_cursor(conn, dictionary=True):
    """Get a cursor with dictionary results."""
    return conn.cursor(dictionary=dictionary)
