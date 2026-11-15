"""Subject score management: validation, totals, averages, grades and updates."""

import math

from utils import CANCEL, ask, print_error, print_info, print_success, print_warning, separator, timestamp

SUBJECTS = ("CSC301", "CSC309", "CSC299", "CSC303", "ICT305", "CSC305")

# (minimum average, grade, remark) - checked from the top down.
GRADE_BANDS = (
    (70, "A", "Excellent"),
    (60, "B", "Very Good"),
    (50, "C", "Good"),
    (45, "D", "Fair"),
    (0, "F", "Fail"),
)


# --------------------------------------------------------------- calculations
def validate_score(raw):
    """Validate a score typed by the user. Returns (is_valid, score_or_message)."""
    try:
        score = float(raw.strip())
    except ValueError:
        return False, "Score must be a number between 0 and 100."
    if not math.isfinite(score) or not 0 <= score <= 100:
        return False, "Score must be between 0 and 100."
    score = round(score, 2)
    if score == int(score):
        score = int(score)
    return True, score


def count_recorded(scores):
    """How many subjects have a recorded score."""
    return sum(1 for subject in SUBJECTS if scores.get(subject) is not None)


def is_complete(scores):
    """True only when every subject has a score."""
    return count_recorded(scores) == len(SUBJECTS)


def calculate_total(scores):
    """Total of all subject scores, or None if results are incomplete."""
    if not is_complete(scores):
        return None
    return round(sum(scores[subject] for subject in SUBJECTS), 2)


def calculate_average(scores):
    """Average score (2 decimal places), or None if results are incomplete."""
    total = calculate_total(scores)
    if total is None:
        return None
    return round(total / len(SUBJECTS), 2)


def assign_grade(average):
    """Grade for an average score using GRADE_BANDS."""
    for minimum, grade, _ in GRADE_BANDS:
        if average >= minimum:
            return grade
    return "F"


def get_remark(grade):
    for _, band_grade, remark in GRADE_BANDS:
        if band_grade == grade:
            return remark
    return ""


def compute_result(scores):
    """Return {'total','average','grade','remark'} or None if incomplete."""
    average = calculate_average(scores)
    if average is None:
        return None
    grade = assign_grade(average)
    return {
        "total": calculate_total(scores),
        "average": average,
        "grade": grade,
        "remark": get_remark(grade),
    }


# ------------------------------------------------------------------- updates
def stamp_results(student):
    """Record when results were first entered and last updated."""
    now = timestamp()
    if student.results_entered is None:
        student.results_entered = now
    student.results_updated = now


def set_score(student, subject, score):
    """Store a score for one subject and stamp the record."""
    student.scores[subject] = score
    stamp_results(student)


def _print_score_table(student):
    print(separator("-", 40))
    for number, subject in enumerate(SUBJECTS, start=1):
        score = student.scores[subject]
        shown = "Not recorded" if score is None else score
        print(f"{number}. {subject:<20}{shown}")
    print(separator("-", 40))


# --------------------------------------------------------- interactive flows
def record_scores_interactive(student):
    """Collect scores for subjects that have none yet. Returns True if data changed."""
    missing = [s for s in SUBJECTS if student.scores[s] is None]
    if not missing:
        print_info("All subject scores are already recorded. Use 'Update Student Scores' to change them.")
        return False

    print(f"\nRecording scores for {student.name} ({student.student_id}).")
    print("Enter a score from 0 to 100. Press Enter to skip a subject or type 'cancel' to abort.\n")
    entered = {}
    for subject in missing:
        value = ask(f"  {subject:<18}: ", validate_score, blank_value=None)
        if value is CANCEL:
            print_info("Score entry cancelled. Nothing was saved.")
            return False
        if value is not None:
            entered[subject] = value

    if not entered:
        print_info("No scores were entered.")
        return False

    for subject, score in entered.items():
        set_score(student, subject, score)
    print_success(f"Recorded {len(entered)} score(s) for {student.name}.")
    still_missing = [s for s in SUBJECTS if student.scores[s] is None]
    if still_missing:
        print_warning("Results are incomplete (no total/grade yet). Missing: " + ", ".join(still_missing))
    return True


def update_scores_interactive(student):
    """Let the user change (or fill in) individual subject scores. Returns True if changed."""
    if count_recorded(student.scores) == 0:
        print_info("No scores recorded yet. Use 'Record Student Scores' first.")
        return False

    changed = False
    print(f"\nUpdating scores for {student.name} ({student.student_id}).")
    while True:
        _print_score_table(student)
        choice = input("Subject number to update (0 to finish): ").strip()
        if choice == "0":
            break
        if not choice.isdigit() or not 1 <= int(choice) <= len(SUBJECTS):
            print_error(f"Enter a number from 0 to {len(SUBJECTS)}.")
            continue
        subject = SUBJECTS[int(choice) - 1]
        value = ask(f"New score for {subject} (0-100, or 'cancel'): ", validate_score)
        if value is CANCEL:
            continue
        set_score(student, subject, value)
        changed = True
        print_success(f"{subject} updated to {value}.")
    return changed
