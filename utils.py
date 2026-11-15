"""Shared helper functions: validation, input prompts and console formatting."""

import re
from datetime import date, datetime

LINE_WIDTH = 78
CANCEL = object()      # returned by ask() when the user types 'cancel'
_UNSET = object()      # marks "no blank value allowed" in ask()


# ----------------------------------------------------------------- display
def separator(char="-", width=LINE_WIDTH):
    """Return a horizontal line made of `char`."""
    return char * width


def print_header(title):
    """Print a centred, upper-case section title between two lines."""
    print()
    print(separator("="))
    print(title.upper().center(LINE_WIDTH))
    print(separator("="))


def print_success(message):
    print(f"[SUCCESS] {message}")


def print_error(message):
    print(f"[ERROR] {message}")


def print_info(message):
    print(f"[INFO] {message}")


def print_warning(message):
    print(f"[WARNING] {message}")


def truncate(text, width):
    """Shorten text with '...' so it fits into `width` characters."""
    text = str(text)
    return text if len(text) <= width else text[: width - 3] + "..."


def timestamp():
    """Current local date and time as 'YYYY-MM-DD HH:MM:SS'."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# -------------------------------------------------------------- validators
# Every validator takes the raw text and returns (is_valid, value_or_message).
def validate_student_id(raw):
    value = raw.strip().upper()
    if not value:
        return False, "Student ID cannot be empty."
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9/_-]{0,19}", value):
        return False, ("Student ID may contain only letters, digits, '-', '_' "
                       "and '/' (maximum 20 characters).")
    return True, value


def validate_name(raw):
    value = " ".join(raw.split())
    if not value:
        return False, "Name cannot be empty."
    if len(value) > 60:
        return False, "Name must not exceed 60 characters."
    if not re.fullmatch(r"[A-Za-z.'-]+(?: [A-Za-z.'-]+)+", value):
        return False, ("Enter the full name (at least two words) using letters, "
                       "spaces, '.', '-' and apostrophes only.")
    if value.islower() or value.isupper():
        value = value.title()
    return True, value


def validate_class(raw):
    value = " ".join(raw.split()).upper()
    if not value:
        return False, "Class/Form cannot be empty."
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9 /-]{0,19}", value):
        return False, "Class/Form may contain letters, digits, spaces, '-' and '/' (max 20)."
    return True, value


def validate_gender(raw):
    value = raw.strip().lower()
    if value in ("m", "male"):
        return True, "Male"
    if value in ("f", "female"):
        return True, "Female"
    return False, "Enter M/Male or F/Female."


def validate_dob(raw):
    """Accept a real, non-future date written as YYYY-MM-DD (not older than 100 years)."""
    text = raw.strip()
    try:
        born = datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return False, "Enter a valid date in YYYY-MM-DD format (e.g. 2008-03-15)."
    else:
        today = date.today()
        if born > today:
            return False, "Date of birth cannot be in the future."
        if calculate_age(text) > 100:
            return False, "Date of birth is not realistic (over 100 years ago)."
        return True, born.isoformat()


def calculate_age(dob_text, today=None):
    """Age in whole years for a 'YYYY-MM-DD' date of birth."""
    today = today or date.today()
    born = datetime.strptime(dob_text, "%Y-%m-%d").date()
    years = today.year - born.year
    if (today.month, today.day) < (born.month, born.day):
        years -= 1
    return years


# ------------------------------------------------------------ input helpers
def ask(prompt, validator, blank_value=_UNSET):
    """Prompt until `validator` accepts the input.

    Returns the validated value, CANCEL if the user types 'cancel', or
    `blank_value` if one was supplied and the user just pressed Enter.
    """
    while True:
        raw = input(prompt).strip()
        if raw.lower() == "cancel":
            return CANCEL
        if raw == "" and blank_value is not _UNSET:
            return blank_value
        is_valid, result = validator(raw)
        if is_valid:
            return result
        print_error(result)


def confirm(prompt):
    """Ask a yes/no question and return True for yes."""
    while True:
        answer = input(f"{prompt} (y/n): ").strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print_error("Please answer 'y' or 'n'.")


def pause():
    input("\nPress Enter to return to the main menu...")
