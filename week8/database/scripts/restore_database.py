import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from db_schema_constants import CORE_TABLES, CORE_VIEWS
import re

load_dotenv()
DEFAULT_DB = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432"),
    "user": os.environ.get("DB_USER", "datavision"),
    "dbname": os.environ.get("DB_NAME", "datavision_db"),
}


class RestoreFailed(Exception):
    pass


def log(msg):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] [restore] {msg}", flush=True)


def get_db_password():
    password = os.environ.get("DB_PASSWORD")
    if not password:
        raise RestoreFailed(
            "DB_PASSWORD environment variable is not set. "
            "Refusing to run with a default/hard-coded credential."
        )
    return password


def run_cmd(cmd, step_name, env, check=True):
    log(f"--- {step_name} ---")
    log("Command: " + " ".join(str(c) for c in cmd))
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if result.stdout.strip():
        log(result.stdout.strip())
    if result.returncode != 0:
        msg = f"{step_name} failed (exit {result.returncode}): {result.stderr.strip()}"
        if check:
            raise RestoreFailed(msg)
        log(f"WARNING: {msg}")
        return False
    return True


def get_pg_cmd(cmd_name, pg_bin_dir=""):
    if pg_bin_dir:
        return os.path.join(pg_bin_dir, cmd_name)
    return cmd_name


def verify_dump_file(dump_file: Path, env, pg_bin_dir=""):
    if not dump_file.exists() or dump_file.stat().st_size == 0:
        raise RestoreFailed(f"Dump file missing or empty: {dump_file}")

    cmd = get_pg_cmd("pg_restore", pg_bin_dir)
    run_cmd(
        [cmd, "--list", str(dump_file)],
        "Verify dump file is readable (pg_restore --list)",
        env=env,
    )


def drop_database(db, env, force: bool, pg_bin_dir=""):
    if not force and db["dbname"] == DEFAULT_DB["dbname"]:
        raise RestoreFailed(
            f"Refusing to drop '{db['dbname']}' without --force. "
            "This looks like the live database name; pass a *_restore_test "
            "name for a rehearsal, or --force for a deliberate real restore."
        )

    cmd = get_pg_cmd("dropdb", pg_bin_dir)
    run_cmd(
        [cmd, "-h", db["host"], "-p", db["port"], "-U", db["user"],
         "--if-exists", db["dbname"]],
        f"Drop database {db['dbname']} (if exists)",
        env=env,
    )


def create_database(db, env, pg_bin_dir=""):
    cmd = get_pg_cmd("createdb", pg_bin_dir)
    run_cmd(
        [cmd, "-h", db["host"], "-p", db["port"], "-U", db["user"],
         db["dbname"]],
        f"Create database {db['dbname']}",
        env=env,
    )


# No blanket-ignore patterns. Any pg_restore error must be added here
# explicitly, by exact identified pattern, after review — never a generic
# catch-all — or the restore is treated as FAILED (DV-PHAT-03).
ALLOWED_RESTORE_ERROR_PATTERNS: list[str] = []


def pg_restore(db, dump_file: Path, env, pg_bin_dir=""):
    cmd = get_pg_cmd("pg_restore", pg_bin_dir)
    result = subprocess.run(
        [cmd, "-h", db["host"], "-p", db["port"], "-U", db["user"],
         "-d", db["dbname"], "--no-owner", "--no-privileges", str(dump_file)],
        env=env, capture_output=True, text=True,
    )
    log(f"--- pg_restore into {db['dbname']} ---")
    if result.stdout.strip():
        log(result.stdout.strip())

    if result.returncode != 0:
        stderr_lines = [l for l in result.stderr.strip().splitlines() if l.strip()]
        unallowed = [
            line for line in stderr_lines
            if not any(re.search(p, line) for p in ALLOWED_RESTORE_ERROR_PATTERNS)
        ]
        if unallowed:
            raise RestoreFailed(
                f"pg_restore failed (exit {result.returncode}) with unreviewed "
                f"errors:\n" + "\n".join(unallowed)
            )
        # Even if every line matched a reviewed pattern, a non-zero exit
        # from pg_restore is never silently downgraded to PASS.
        raise RestoreFailed(
            f"pg_restore exited {result.returncode}. All stderr lines matched "
            f"reviewed patterns, but DV-PHAT-03 requires exit code 0, not a "
            f"whitelisted warning:\n" + "\n".join(stderr_lines)
        )
    log("pg_restore completed with exit code 0.")


def get_row_counts(db, env):
    """Connect to the restored DB and collect row counts + extension check."""
    import psycopg2

    conn = psycopg2.connect(
        host=db["host"], port=db["port"], user=db["user"],
        password=env["PGPASSWORD"], dbname=db["dbname"],
    )
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


def compare_counts(restored: dict, reference: dict):
    mismatches = []
    for key, ref_val in reference.items():
        restored_val = restored.get(key)
        if restored_val != ref_val:
            mismatches.append(
                {"key": key, "expected": ref_val, "restored": restored_val}
            )
    return mismatches


def main():
    parser = argparse.ArgumentParser(description="Week 8 database restore procedure")
    parser.add_argument("--dump-file", required=True, help="Path to .dump file to restore")
    parser.add_argument("--host", default=DEFAULT_DB["host"])
    parser.add_argument("--port", default=DEFAULT_DB["port"])
    parser.add_argument("--user", default=DEFAULT_DB["user"])
    parser.add_argument(
        "--dbname",
        default=f"{DEFAULT_DB['dbname']}_restore_test",
        help="Target database to restore into "
             "(default: <dbname>_restore_test, so rehearsals never touch the live DB)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow restoring into the live database name (real DR event, not a rehearsal)",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="After restore, check pgvector + row counts on the restored DB",
    )
    parser.add_argument(
        "--reference-counts",
        help="Optional JSON file with expected row counts to diff against "
             "(e.g. captured by backup_database.py before the dump was taken)",
    )
    parser.add_argument(
        "--output",
        default="week8/database/outputs/db_validation/restore_result.json",
        help="Where to write the restore/verification report",
    )
    parser.add_argument(
        "--pg-bin-dir",
        default=os.environ.get("PG_BIN_DIR", ""),
        help="Path to PostgreSQL binaries (e.g. D:\\Postgresql16\\pgsql\\bin). "
             "If omitted, relies on system PATH.",
    )

    args = parser.parse_args()

    db = {"host": args.host, "port": args.port, "user": args.user, "dbname": args.dbname}
    dump_file = Path(args.dump_file)

    try:
        password = get_db_password()
    except RestoreFailed as e:
        log(f"ERROR: {e}")
        return 1

    env = os.environ.copy()
    env["PGPASSWORD"] = password

    log("=" * 70)
    log("Week 8 Database Restore Procedure (DV-PHAT-03)")
    log(f"Dump file: {dump_file}")
    log(f"Target DB: {db['user']}@{db['host']}:{db['port']}/{db['dbname']}")
    if args.pg_bin_dir:
        log(f"PG Bin Dir: {args.pg_bin_dir}")
    log("=" * 70)

    report = {
        "dump_file": str(dump_file),
        "target_db": db["dbname"],
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    try:
        verify_dump_file(dump_file, env, args.pg_bin_dir)
        drop_database(db, env, args.force, args.pg_bin_dir)
        create_database(db, env, args.pg_bin_dir)
        pg_restore(db, dump_file, env, args.pg_bin_dir)
        report["restore_status"] = "success"
        log("Restore completed.")

        if args.verify:
            counts = get_row_counts(db, env)
            report["counts"] = counts
            log(f"Post-restore counts: {json.dumps(counts, indent=2)}")

            if not counts.get("pgvector_extension_present"):
                raise RestoreFailed("pgvector extension missing after restore")

            if args.reference_counts:
                ref_path = Path(args.reference_counts)
                manifest_data = json.loads(ref_path.read_text())

                if "counts" in manifest_data:
                    reference = manifest_data["counts"]
                else:
                    metadata_keys = ["timestamp", "path", "checksum", "size", "format"]
                    reference = {k: v for k, v in manifest_data.items() if k not in metadata_keys}

                mismatches = compare_counts(counts, reference)
                report["reference_counts_file"] = str(ref_path)
                report["mismatches"] = mismatches
                if mismatches:
                    raise RestoreFailed(
                        f"Row count mismatch vs reference: {mismatches}"
                    )
                log("Row counts match reference. Restore verified.")

        report["overall_result"] = "PASS"

    except RestoreFailed as e:
        report["overall_result"] = "FAIL"
        report["error"] = str(e)
        log("!" * 70)
        log(f"RESTORE FAILED: {e}")
        log("!" * 70)
        _write_report(args.output, report)
        return 1

    _write_report(args.output, report)
    log(f"Report written to {args.output}")
    return 0


def _write_report(output_path: str, report: dict):
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    report["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    out.write_text(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    sys.exit(main())