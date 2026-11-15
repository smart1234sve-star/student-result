"""Student Result Management System - application entry point and main menu."""

import sys

import reports
from results import record_scores_interactive, update_scores_interactive
from storage import DB_FILE, load_students, save_students
from student import (
    delete_student_interactive, register_student_interactive, search_students,
    select_student, update_student_interactive,
)
from utils import (
    LINE_WIDTH, confirm, pause, print_error, print_header, print_info,
    print_success, print_warning, separator,
)

MENU = (
    "Register New Student",
    "View All Students",
    "Search Student",
    "Update Student Information",
    "Delete Student",
    "Record Student Scores",
    "Update Student Scores",
    "View Individual Report Card",
    "View All Student Results",
    "Rank Students",
    "View Class Statistics",
    "Generate Academic Report",
    "Exit Application",
)


def show_welcome():
    print(separator("*"))
    print("STUDENT RESULT MANAGEMENT SYSTEM".center(LINE_WIDTH))
    print("New Horizon - Introduction to Python Programming".center(LINE_WIDTH))
    print("Smart Samuel Oluwaseyi - 24/sci01/195".center(LINE_WIDTH))
    print(separator("*"))


def show_menu():
    print_header("Main Menu")
    for number, label in enumerate(MENU, start=1):
        print(f"  {number:>2}. {label}")
    print(separator("-"))


def ask_sort_mode():
    """Ask how a list should be ordered."""
    print("\nSort by: 1) Registration order   2) Name (A-Z)   3) Student ID")
    choice = input("Choose 1-3 [1]: ").strip()
    return {"2": "name", "3": "id"}.get(choice, "registered")


def offer_to_save(text, prefix):
    """Offer to save generated text to a file in generated_reports/."""
    if confirm("\nSave this to a text file?"):
        try:
            path = reports.save_report(text, prefix)
        except OSError as error:
            print_error(f"Could not save the file: {error}")
        else:
            print_success(f"Saved to {path}")


def require_students(students):
    if not students:
        print_info("No students are registered yet.")
        return False
    return True


# ------------------------------------------------------------------ handlers
# Each handler returns True when it changed data that must be saved.
def handle_register(students):
    print_header("Register New Student")
    return register_student_interactive(students)


def handle_view_all(students):
    print_header("All Registered Students")
    if require_students(students):
        print(reports.format_students_table(reports.sort_students(students.values(), ask_sort_mode())))
    return False


def handle_search(students):
    print_header("Search Student")
    if not require_students(students):
        return False
    query = input("Enter Student ID or part of the name (or 'cancel'): ").strip()
    if query.lower() == "cancel" or not query:
        print_info("Search cancelled.")
        return False
    matches = search_students(students, query)
    if matches:
        print(reports.format_students_table(matches))
    else:
        print_error(f"No student found matching '{query}'.")
    return False


def handle_update_student(students):
    print_header("Update Student Information")
    student = select_student(students)
    return update_student_interactive(student) if student else False


def handle_delete(students):
    print_header("Delete Student")
    student = select_student(students)
    return delete_student_interactive(students, student) if student else False


def handle_record_scores(students):
    print_header("Record Student Scores")
    student = select_student(students)
    return record_scores_interactive(student) if student else False


def handle_update_scores(students):
    print_header("Update Student Scores")
    student = select_student(students)
    return update_scores_interactive(student) if student else False


def handle_report_card(students):
    print_header("Individual Report Card")
    student = select_student(students)
    if student:
        card = reports.format_report_card(student, list(students.values()))
        print(card)
        offer_to_save(card, f"report_card_{student.student_id}")
    return False


def handle_all_results(students):
    print_header("All Student Results")
    if require_students(students):
        ordered = reports.sort_students(students.values(), ask_sort_mode())
        print(reports.format_results_table(ordered))
    return False


def handle_ranking(students):
    print_header("Student Ranking")
    if require_students(students):
        print(reports.format_ranking_table(list(students.values())))
    return False


def handle_statistics(students):
    print_header("Class Statistics")
    if require_students(students):
        print(reports.format_statistics(reports.class_statistics(list(students.values()))))
    return False


def handle_academic_report(students):
    print_header("Academic Report")
    if require_students(students):
        text = reports.format_academic_report(list(students.values()))
        print(text)
        offer_to_save(text, "academic_report")
    return False


HANDLERS = {
    "1": handle_register, "2": handle_view_all, "3": handle_search,
    "4": handle_update_student, "5": handle_delete, "6": handle_record_scores,
    "7": handle_update_scores, "8": handle_report_card, "9": handle_all_results,
    "10": handle_ranking, "11": handle_statistics, "12": handle_academic_report,
}


def persist(students):
    """Save to disk and tell the user if that fails."""
    try:
        save_students(students)
    except OSError as error:
        print_error(f"Changes could NOT be saved to {DB_FILE}: {error}")
        return False
    return True


def main():
    show_welcome()
    try:
        students, notices = load_students()
    except OSError as error:
        print_error(f"Cannot open the data file: {error}")
        return 1
    for notice in notices:
        print_warning(notice)
    print_info(f"Loaded {len(students)} student record(s).")

    try:
        while True:
            show_menu()
            choice = input(f"Select an option (1-{len(MENU)}): ").strip()
            if choice == str(len(MENU)):
                break
            handler = HANDLERS.get(choice)
            if handler is None:
                print_error(f"Invalid selection '{choice}'. Please enter a number from 1 to {len(MENU)}.")
                continue
            if handler(students):
                if persist(students):
                    print_info("Changes saved.")
            pause()
    except (EOFError, KeyboardInterrupt):
        print()
        print_info("Input ended. Exiting.")

    print_header("Goodbye")
    print("Thank you for using the Student Result Management System.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
