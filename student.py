"""Student class plus registration, lookup, update and deletion logic."""

from results import SUBJECTS, validate_score
from utils import (
    CANCEL, ask, calculate_age, confirm, print_error, print_info, print_success,
    separator, validate_class, validate_dob, validate_gender, validate_name,
    validate_student_id,
)


class Student:
    """A registered student together with their subject scores."""

    def __init__(self, student_id, name, class_name, gender, date_of_birth,
                 scores=None, results_entered=None, results_updated=None):
        self.student_id = student_id
        self.name = name
        self.class_name = class_name
        self.gender = gender
        self.date_of_birth = date_of_birth
        self.scores = {subject: None for subject in SUBJECTS}
        for subject in SUBJECTS:
            if scores and scores.get(subject) is not None:
                self.scores[subject] = scores[subject]
        self.results_entered = results_entered
        self.results_updated = results_updated

    @property
    def age(self):
        return calculate_age(self.date_of_birth)

    def to_dict(self):
        """Plain dictionary suitable for JSON."""
        return {
            "student_id": self.student_id,
            "name": self.name,
            "class_name": self.class_name,
            "gender": self.gender,
            "date_of_birth": self.date_of_birth,
            "scores": dict(self.scores),
            "results_entered": self.results_entered,
            "results_updated": self.results_updated,
        }

    @classmethod
    def from_dict(cls, data):
        """Build a Student from stored data; raise ValueError if the data is invalid."""
        if not isinstance(data, dict):
            raise ValueError("record is not an object")
        fields = {}
        checks = (("student_id", validate_student_id), ("name", validate_name),
                  ("class_name", validate_class), ("gender", validate_gender),
                  ("date_of_birth", validate_dob))
        for key, validator in checks:
            value = data.get(key)
            if not isinstance(value, str):
                raise ValueError(f"missing or invalid '{key}'")
            ok, result = validator(value)
            if not ok:
                raise ValueError(f"'{key}': {result}")
            fields[key] = result

        raw_scores = data.get("scores") or {}
        if not isinstance(raw_scores, dict):
            raise ValueError("'scores' must be an object")
        scores = {}
        for subject in SUBJECTS:
            value = raw_scores.get(subject)
            if value is None:
                continue
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"invalid score for {subject}")
            ok, result = validate_score(str(value))
            if not ok:
                raise ValueError(f"{subject}: {result}")
            scores[subject] = result

        return cls(fields["student_id"], fields["name"], fields["class_name"],
                   fields["gender"], fields["date_of_birth"], scores,
                   data.get("results_entered"), data.get("results_updated"))

    def summary(self):
        """Multi-line description used when confirming actions."""
        return (f"  Student ID    : {self.student_id}\n"
                f"  Full Name     : {self.name}\n"
                f"  Class/Form    : {self.class_name}\n"
                f"  Gender        : {self.gender}\n"
                f"  Date of Birth : {self.date_of_birth} (age {self.age})")

    def __str__(self):
        return f"{self.student_id} - {self.name} ({self.class_name})"


# ------------------------------------------------------------ core operations
def add_student(students, student):
    """Add a student; raise ValueError if the ID already exists."""
    if student.student_id in students:
        raise ValueError(f"Student ID '{student.student_id}' already exists.")
    students[student.student_id] = student


def get_student(students, student_id):
    """Exact lookup by ID (case-insensitive). Returns None when not found."""
    return students.get(student_id.strip().upper())


def search_students(students, query):
    """Students whose ID equals the query or whose name contains it."""
    query = query.strip().lower()
    if not query:
        return []
    return [s for s in students.values()
            if s.student_id.lower() == query or query in s.name.lower()]


def delete_student(students, student_id):
    """Remove and return a student; raise KeyError if the ID is unknown."""
    return students.pop(student_id.strip().upper())


# --------------------------------------------------------- interactive flows
def register_student_interactive(students):
    """Prompt for a new student's details. Returns True if a student was added."""
    print("\nEnter the student's details (type 'cancel' at any prompt to abort).\n")

    def unique_id(raw):
        ok, result = validate_student_id(raw)
        if ok and result in students:
            return False, f"Student ID '{result}' is already registered."
        return ok, result

    prompts = (("Student ID", unique_id), ("Full Name", validate_name),
               ("Class/Form (e.g. SS 2A)", validate_class),
               ("Gender (M/F)", validate_gender),
               ("Date of Birth (YYYY-MM-DD)", validate_dob))
    values = []
    for label, validator in prompts:
        value = ask(f"{label}: ", validator)
        if value is CANCEL:
            print_info("Registration cancelled.")
            return False
        values.append(value)

    student = Student(*values)
    add_student(students, student)
    print_success(f"Student registered:\n{student.summary()}")
    return True


def select_student(students):
    """Ask for an ID or name and return the matching Student (or None)."""
    if not students:
        print_info("No students are registered yet.")
        return None
    query = input("Enter Student ID or name (or 'cancel'): ").strip()
    if query.lower() == "cancel":
        return None
    exact = get_student(students, query)
    if exact:
        return exact
    matches = search_students(students, query)
    if not matches:
        print_error(f"No student found matching '{query}'.")
        return None
    if len(matches) == 1:
        return matches[0]

    print_info(f"{len(matches)} students match. Please choose one:")
    for match in matches:
        print(f"  {match.student_id:<12} {match.name} ({match.class_name})")

    def known_id(raw):
        student = get_student(students, raw)
        if student and student in matches:
            return True, student
        return False, "Enter one of the Student IDs listed above."

    chosen = ask("Student ID: ", known_id)
    return None if chosen is CANCEL else chosen


def update_student_interactive(student):
    """Edit a student's details; blank input keeps the current value. Returns True if changed."""
    print(f"\nCurrent details:\n{student.summary()}")
    print("\nPress Enter to keep a value, or type 'cancel' to abort. (Student ID cannot be changed.)\n")
    fields = (("name", "Full Name", validate_name),
              ("class_name", "Class/Form", validate_class),
              ("gender", "Gender (M/F)", validate_gender),
              ("date_of_birth", "Date of Birth (YYYY-MM-DD)", validate_dob))
    new_values = {}
    for attribute, label, validator in fields:
        current = getattr(student, attribute)
        value = ask(f"{label} [{current}]: ", validator, blank_value=current)
        if value is CANCEL:
            print_info("Update cancelled. No changes were made.")
            return False
        new_values[attribute] = value

    if all(getattr(student, k) == v for k, v in new_values.items()):
        print_info("No changes were made.")
        return False
    for attribute, value in new_values.items():
        setattr(student, attribute, value)
    print_success(f"Student updated:\n{student.summary()}")
    return True


def delete_student_interactive(students, student):
    """Confirm and delete a student. Returns True if deleted."""
    print(f"\nYou are about to delete this student and all their scores:\n{student.summary()}")
    if not confirm("Are you sure you want to permanently delete this record?"):
        print_info("Deletion cancelled. The record was kept.")
        return False
    delete_student(students, student.student_id)
    print_success(f"Student {student.student_id} ({student.name}) was deleted.")
    return True
