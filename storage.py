"""JSON persistence: creating, loading, saving and recovering the student database."""

import json
import os
import shutil
from datetime import datetime

from student import Student
from utils import timestamp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_FILE = os.path.join(DATA_DIR, "students.json")
DB_VERSION = 1


def _write_json(path, payload):
    """Write JSON safely: write to a temporary file, then replace the real one."""
    temp_path = path + ".tmp"
    try:
        with open(temp_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        if os.path.exists(temp_path):   # only true if something failed above
            os.remove(temp_path)


def ensure_storage(db_path=DB_FILE):
    """Create the data directory and an empty database file if they do not exist."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    if not os.path.exists(db_path):
        _write_json(db_path, {"version": DB_VERSION, "last_saved": timestamp(), "students": []})


def _backup(db_path):
    """Copy the current file aside so its content is never lost. Returns backup path."""
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.bak-{stamp}"
    shutil.copy2(db_path, backup_path)
    return backup_path


def load_students(db_path=DB_FILE):
    """Load all students. Returns (students_dict, notices).

    Missing files are created, empty files are treated as an empty database,
    and corrupted files are backed up before the system starts with what
    could be recovered. `notices` lists messages to show the user.
    """
    notices = []
    ensure_storage(db_path)

    try:
        with open(db_path, "r", encoding="utf-8") as handle:
            content = handle.read()
    except UnicodeDecodeError:
        backup = _backup(db_path)
        notices.append(f"The database file could not be read. A copy was saved as '{backup}'. Starting empty.")
        return {}, notices

    if not content.strip():
        notices.append("The database file was empty. Starting with no students.")
        return {}, notices

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        backup = _backup(db_path)
        notices.append(f"The database file was corrupted. A copy was saved as '{backup}'. Starting empty.")
        return {}, notices

    records = data.get("students") if isinstance(data, dict) else None
    if not isinstance(records, list):
        backup = _backup(db_path)
        notices.append(f"The database file has an unexpected structure. A copy was saved as '{backup}'. Starting empty.")
        return {}, notices

    students = {}
    skipped = 0
    for record in records:
        try:
            student = Student.from_dict(record)
        except ValueError:
            skipped += 1
            continue
        if student.student_id in students:
            skipped += 1        # duplicate ID: keep the first record
            continue
        students[student.student_id] = student
    if skipped:
        backup = _backup(db_path)
        notices.append(f"{skipped} invalid or duplicate record(s) were skipped. "
                       f"The original file was backed up as '{backup}'.")
    return students, notices


def save_students(students, db_path=DB_FILE):
    """Write every student to the JSON database."""
    ensure_storage(db_path)
    payload = {
        "version": DB_VERSION,
        "last_saved": timestamp(),
        "students": [student.to_dict() for student in students.values()],
    }
    _write_json(db_path, payload)
