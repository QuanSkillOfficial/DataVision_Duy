import os
import psycopg2


def get_db_connection():
    password = os.environ.get("DB_PASSWORD")
    if not password:
        raise RuntimeError(
            "DB_PASSWORD environment variable is required. "
            "Set it before running this script, e.g.:\n"
            "  export DB_PASSWORD='your-password'"
        )
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=os.environ.get("DB_PORT", "5432"),
        dbname=os.environ.get("DB_NAME", "datavision_db"),
        user=os.environ.get("DB_USER", "datavision"),
        password=password,
    )
