import os
import sys
import json
import hashlib
import subprocess
from datetime import datetime
from dotenv import load_dotenv
from db_schema_constants import CORE_TABLES, CORE_VIEWS

load_dotenv()


def get_row_counts(db_host, db_port, db_user, db_name, password):
    import psycopg2
    conn = psycopg2.connect(host=db_host, port=db_port, user=db_user,
                             password=password, dbname=db_name)
    counts = {}
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT extname FROM pg_extension WHERE extname = 'vector';")
            counts["pgvector_extension_present"] = cur.fetchone() is not None
            for table in CORE_TABLES:
                cur.execute(f"SELECT COUNT(*) FROM {table};")
                counts[table] = cur.fetchone()[0]
            for view in CORE_VIEWS:
                cur.execute(f"SELECT COUNT(*) FROM {view};")
                counts[f"view:{view}"] = cur.fetchone()[0]
    finally:
        conn.close()
    return counts


def main():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join("week8", "database", "outputs", "backups")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, f"datavision_db_{ts}.dump")

    db_host = os.environ.get("DB_HOST", "localhost")
    db_port = os.environ.get("DB_PORT", "5432")
    db_user = os.environ.get("DB_USER", "datavision")
    db_name = os.environ.get("DB_NAME", "datavision_db")
    pg_bin_dir = os.environ.get("PG_BIN_DIR", "")

    password = os.environ.get("DB_PASSWORD")
    if not password:
        sys.stderr.write("DB_PASSWORD environment variable is required — ABORT\n")
        sys.exit(1)

    env = os.environ.copy()
    env["PGPASSWORD"] = password

    pg_dump_cmd = os.path.join(pg_bin_dir, "pg_dump") if pg_bin_dir else "pg_dump"
    dump_cmd = [pg_dump_cmd, "-h", db_host, "-p", db_port, "-U", db_user,
                "-d", db_name, "-F", "c", "-f", out_file]

    try:
        subprocess.run(dump_cmd, env=env, check=True, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"pg_dump failed — ABORT\n{e.stderr.decode(errors='replace')}\n")
        sys.exit(1)

    if not os.path.exists(out_file) or os.path.getsize(out_file) == 0:
        sys.stderr.write("Backup file empty — ABORT\n")
        sys.exit(1)

    pg_restore_cmd = os.path.join(pg_bin_dir, "pg_restore") if pg_bin_dir else "pg_restore"
    try:
        subprocess.run([pg_restore_cmd, "--list", out_file], env=env, check=True,
                        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Backup unreadable — ABORT\n{e.stderr.decode(errors='replace')}\n")
        sys.exit(1)

    sha256_hash = hashlib.sha256()
    with open(out_file, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    checksum = sha256_hash.hexdigest()

    with open(f"{out_file}.sha256", "w") as f:
        f.write(f"{checksum}  {os.path.basename(out_file)}\n")

    try:
        counts = get_row_counts(db_host, db_port, db_user, db_name, password)
    except Exception as e:
        sys.stderr.write(f"Could not capture reference row counts: {e}\n")
        sys.exit(1)

    manifest = {
        "timestamp": ts,
        "path": out_file,
        "checksum": checksum,
        "size": os.path.getsize(out_file),
        "counts": counts,
    }

    manifest_file = os.path.join(out_dir, "backup_manifest.json")
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=4)

    sys.stdout.write(f"Backup OK: {out_file}\n")


if __name__ == "__main__":
    main()