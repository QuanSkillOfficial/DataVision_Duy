import os
import sys
import json
import hashlib
import subprocess
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
def main():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join("week8", "database", "outputs", "backups")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, f"datavision_db_{ts}.dump")

    db_host = os.environ.get("DB_HOST", "localhost")
    db_port = os.environ.get("DB_PORT", "5432")
    db_user = os.environ.get("DB_USER", "datavision")
    db_name = os.environ.get("DB_NAME", "datavision_db")
    
    env = os.environ.copy()
    if "DB_PASSWORD" in env:
        env["PGPASSWORD"] = env["DB_PASSWORD"]

    dump_cmd = [
        "pg_dump", 
        "-h", db_host, 
        "-p", db_port, 
        "-U", db_user, 
        "-d", db_name, 
        "-F", "c", 
        "-f", out_file
    ]
    
    try:
        subprocess.run(dump_cmd, env=env, check=True, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        sys.exit(1)

    if not os.path.exists(out_file) or os.path.getsize(out_file) == 0:
        sys.stderr.write("Backup file empty — ABORT\n")
        sys.exit(1)

    try:
        subprocess.run(
            ["pg_restore", "--list", out_file], 
            env=env, 
            check=True, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError:
        sys.stderr.write("Backup unreadable — ABORT\n")
        sys.exit(1)

    sha256_hash = hashlib.sha256()
    with open(out_file, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    checksum = sha256_hash.hexdigest()

    with open(f"{out_file}.sha256", "w") as f:
        f.write(f"{checksum}  {os.path.basename(out_file)}\n")

    manifest = {
        "timestamp": ts,
        "path": out_file,
        "checksum": checksum,
        "size": os.path.getsize(out_file)
    }

    manifest_file = os.path.join(out_dir, "backup_manifest.json")
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=4)

    sys.stdout.write(f"Backup OK: {out_file}\n")

if __name__ == "__main__":
    main()