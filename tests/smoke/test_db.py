"""
Smoke tests for PostgreSQL database connectivity and basic operations.
These tests ensure the database is running and accessible.
"""

import os

import psycopg2
import pytest


class TestDatabaseSmoke:
    """Comprehensive database smoke tests."""

    # Database connection parameters
    DB_CONFIG = {
        "dbname": os.getenv("POSTGRES_DB", "ninaivalaigal_dev"),
        "user": os.getenv("POSTGRES_USER", "nina"),
        "password": os.getenv("POSTGRES_PASSWORD", "secure_nina_password"),
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5432")),
    }

    def get_connection(self) -> psycopg2.extensions.connection:
        """Get database connection with proper error handling."""
        try:
            conn = psycopg2.connect(**self.DB_CONFIG)
            return conn
        except Exception as e:
            pytest.fail(f"Failed to connect to database: {e}")

    def test_postgres_connection(self):
        """Test basic PostgreSQL connection."""
        try:
            conn = self.get_connection()
            assert conn is not None
            assert not conn.closed
            conn.close()
        except Exception as e:
            pytest.fail(f"Postgres connection test failed: {e}")

    def test_postgres_basic_query(self):
        """Test basic SQL query execution."""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute("SELECT 1 as test_value;")
            result = cur.fetchone()
            assert result[0] == 1
            cur.close()
            conn.close()
        except Exception as e:
            pytest.fail(f"Postgres basic query test failed: {e}")

    def test_postgres_version(self):
        """Test PostgreSQL version check."""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
            assert "PostgreSQL" in version
            assert "15" in version  # Expecting PostgreSQL 15
            cur.close()
            conn.close()
        except Exception as e:
            pytest.fail(f"Postgres version check failed: {e}")

    def test_postgres_extensions(self):
        """Test that required extensions are available."""
        try:
            conn = self.get_connection()
            cur = conn.cursor()

            # Check for pgvector extension (if used)
            cur.execute(
                """
                SELECT EXISTS(
                    SELECT 1 FROM pg_available_extensions
                    WHERE name = 'vector'
                );
            """
            )
            vector_available = cur.fetchone()[0]

            # Check for uuid extension
            cur.execute(
                """
                SELECT EXISTS(
                    SELECT 1 FROM pg_available_extensions
                    WHERE name = 'uuid-ossp'
                );
            """
            )
            uuid_available = cur.fetchone()[0]

            # At least one should be available
            assert vector_available or uuid_available, "No expected extensions found"

            cur.close()
            conn.close()
        except Exception as e:
            pytest.fail(f"Postgres extensions check failed: {e}")

    def test_postgres_database_exists(self):
        """Test that the application database exists."""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT EXISTS(
                    SELECT 1 FROM pg_database
                    WHERE datname = %s
                );
            """,
                (self.DB_CONFIG["dbname"],),
            )
            db_exists = cur.fetchone()[0]
            assert db_exists, f"Database {self.DB_CONFIG['dbname']} does not exist"
            cur.close()
            conn.close()
        except Exception as e:
            pytest.fail(f"Database existence check failed: {e}")

    def test_postgres_connection_pool(self):
        """Test multiple concurrent connections."""
        connections = []
        try:
            # Create multiple connections
            for i in range(3):
                conn = self.get_connection()
                connections.append(conn)

            # Test that all connections work
            for i, conn in enumerate(connections):
                cur = conn.cursor()
                cur.execute("SELECT %s as connection_id;", (i,))
                result = cur.fetchone()[0]
                assert result == i
                cur.close()

        except Exception as e:
            pytest.fail(f"Connection pool test failed: {e}")
        finally:
            # Clean up connections
            for conn in connections:
                if not conn.closed:
                    conn.close()

    def test_postgres_transaction_support(self):
        """Test transaction support."""
        try:
            conn = self.get_connection()
            cur = conn.cursor()

            # Start transaction
            conn.autocommit = False

            # Create a temporary table
            cur.execute(
                """
                CREATE TEMPORARY TABLE smoke_test_table (
                    id SERIAL PRIMARY KEY,
                    test_value TEXT
                );
            """
            )

            # Insert test data
            cur.execute(
                """
                INSERT INTO smoke_test_table (test_value)
                VALUES ('test_transaction');
            """
            )

            # Verify data exists
            cur.execute("SELECT test_value FROM smoke_test_table WHERE id = 1;")
            result = cur.fetchone()
            assert result[0] == "test_transaction"

            # Rollback transaction
            conn.rollback()

            cur.close()
            conn.close()

        except Exception as e:
            pytest.fail(f"Transaction support test failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
