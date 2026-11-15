# Student Result Management System

A menu-driven, terminal-based application written in Python for registering students, recording subject scores, calculating results, generating report cards and analysing class performance. Data is stored in a JSON file, so records survive between runs.

---

## 1. Project Overview

The Student Result Management System simulates the everyday work of a school records office. An authorised user can register students, enter and correct their scores, and instantly see totals, averages, grades, class rankings and class statistics. Reports can be printed on screen or saved as text files.

Built as a practical project for the **Introduction to Python Programming** course at **New Horizon**.

## 2. Purpose

- Give secondary schools, educational centres and academic administrators a simple tool for managing results without spreadsheets.
- Demonstrate practical use of core and intermediate Python: functions, classes, file handling, JSON, exceptions, sorting, date/time handling and modular design.

## 3. Key Features

| Area | Features |
|------|----------|
| **Student management** | Register, view (table), search by ID or name, update, delete (with confirmation), duplicate-ID prevention, full input validation |
| **Scores and results** | Six default subjects (course codes), scores validated to 0-100, total, average, automatic grade, report cards, date/time of entry and update |
| **Reporting** | All results with totals/averages/grades, ranking (ties handled), alphabetical sorting, class statistics, text academic report, save reports to `.txt` |
| **Storage** | JSON persistence, auto-created data folder and database, safe writes, recovery from missing, empty or corrupted files |
| **Interface** | Welcome screen, numbered menu, aligned tables, clear `[SUCCESS]`/`[ERROR]` messages, `cancel` at any prompt |

Students whose results are **incomplete** (not all six subjects recorded) are shown as "Incomplete" and are **excluded** from rankings and class statistics.

## 4. Technologies and Python Modules Used

- **Python 3.8 or newer** (standard library only, no third-party packages)
- `json` - reading and writing the database
- `os` - folders, paths, safe file replacement
- `datetime` - timestamps, date-of-birth validation, age calculation
- `re` - input pattern validation
- `math` - rejecting `nan`/`inf` scores
- `shutil` - backing up damaged data files
- `sys` - exit codes
- `unittest`, `subprocess`, `tempfile` - automated tests

## 5. Project Directory Structure

```
student_result_system/
|
+-- main.py                 Entry point, main menu, application loop
+-- student.py              Student class; register, search, update, delete
+-- results.py              Subjects, score validation, total/average/grade, score entry
+-- storage.py              JSON database: create, load, save, recover
+-- reports.py              Tables, report cards, ranking, statistics, text reports
+-- utils.py                Validators, input helpers, console formatting
|
+-- data/
|   +-- students.json       JSON database (created automatically)
+-- generated_reports/      Saved text reports
+-- tests/
|   +-- test_system.py      Automated tests (additional module)
|
+-- README.md
+-- .gitignore
```

Module dependencies run one way only (no circular imports):
`utils` <- `results` <- `student` <- `storage`, and `utils` <- `results` <- `reports`; `main` uses all of them.

## 6. System Requirements

- Python 3.8 or newer
- Any operating system with a terminal (Windows, macOS, Linux)
- No internet connection, database server, or paid software

## 7. Installation

1. Install Python from <https://www.python.org/downloads/> if needed.
2. Download or copy the `student_result_system` folder.
3. Open a terminal in that folder:

```bash
cd student_result_system
python --version        # on macOS/Linux you may need: python3 --version
```

No `pip install` step is needed.

## 8. How to Run the Application

```bash
python main.py          # Windows
python3 main.py         # macOS / Linux
```

To run the automated tests:

```bash
python -m unittest discover -s tests -v
```

## 9. How to Use the Menu

| # | Option | What it does |
|---|--------|--------------|
| 1 | Register New Student | Asks for ID, full name (two or more words), class/form, gender (M/F) and date of birth (`YYYY-MM-DD`). Rejects duplicate IDs. |
| 2 | View All Students | Table of students; choose registration order, name (A-Z) or ID order. |
| 3 | Search Student | Finds students by exact ID or any part of the name. |
| 4 | Update Student Information | Press Enter to keep a value. The Student ID cannot be changed. |
| 5 | Delete Student | Shows the record and asks for `y/n` confirmation first. |
| 6 | Record Student Scores | Enter 0-100 for each subject that has no score. Press Enter to skip a subject (the result stays incomplete). |
| 7 | Update Student Scores | Pick a subject number and enter a new score; repeat, then `0` to finish. |
| 8 | View Individual Report Card | Select by ID or name; optionally save to a text file. |
| 9 | View All Student Results | Every student's total, average, grade and status; sortable. |
| 10 | Rank Students | Highest to lowest average. Equal averages share a rank (1, 2, 2, 4). |
| 11 | View Class Statistics | Total students, highest/lowest/overall average, grade distribution. |
| 12 | Generate Academic Report | Full class report; optionally save to `generated_reports/`. |
| 13 | Exit Application | Closes the program. |

Type `cancel` at most prompts to abandon the current task and return to the menu. Where a student must be chosen, you can type an ID or a name; if several names match, you are asked to pick an ID.

## 10. Grading System

The grade is based on the student's **average score** (rounded to 2 decimal places):

| Grade | Average | Remark |
|-------|---------|--------|
| A | 70 - 100 | Excellent |
| B | 60 - 69.99 | Very Good |
| C | 50 - 59.99 | Good |
| D | 45 - 49.99 | Fair |
| F | Below 45 | Fail |

Default subjects: CSC301, CSC309, CSC299, CSC303, ICT305, CSC305. Change the `SUBJECTS` tuple in `results.py` to use different subjects (existing JSON records would need matching subject names).

## 11. Data Storage and Persistence

- All records are stored in `data/students.json`.
- On first run the program creates the `data/` folder and an empty database.
- Every add, update or delete is written to disk immediately, and records are reloaded at startup.
- Saving writes to a temporary file and then replaces the real file, so a crash mid-save cannot half-overwrite your data.
- **Recovery:** an empty file starts a fresh database. A corrupted file, wrong structure, or invalid/duplicate records trigger a **backup copy** (`data/students.json.bak-<timestamp>`) before the program continues, so nothing is silently lost. A warning is shown at startup.

Example record:

```json
{
  "student_id": "S001",
  "name": "Ada Lovelace",
  "class_name": "SS 2A",
  "gender": "Female",
  "date_of_birth": "2008-03-15",
  "scores": {"CSC301": 90, "CSC309": 80, "CSC299": 70, "CSC303": 60, "ICT305": 50, "CSC305": 70},
  "results_entered": "2026-11-12 20:52:27",
  "results_updated": "2026-11-12 20:52:27"
}
```

> The database contains personal data. Do not publish a populated `students.json` publicly.

## 12. Python Concepts Demonstrated

| Concept | Where |
|---------|-------|
| Variables, data types, type conversion | `results.validate_score` (`str` to `float`/`int`), throughout |
| Conditionals, `for`/`while` loops | Menu loop in `main.py`, `ask()` in `utils.py`, ranking in `reports.py` |
| Lists, tuples, dictionaries | `SUBJECTS`/`GRADE_BANDS` (tuples), students dict, ranking lists |
| Functions with parameters and return values | Every module, e.g. `calculate_average`, `assign_grade` |
| Sorting | `sorted()` with `key=` in `reports.sort_students` and `rank_students` |
| Input validation | `utils.py` validators, `results.validate_score` |
| Exception handling (`try/except/else/finally`) | `utils.validate_dob` (`else`), `storage._write_json` (`finally`), `storage.load_students`, `main.persist` |
| File handling and JSON | `storage.py`, `reports.save_report` |
| Modular programming and imports | Six modules with one-way dependencies |
| OOP: classes, constructors, methods | `Student` (`__init__`, `to_dict`, `from_dict`, `summary`, `__str__`, `@property age`) |
| Date and time | `datetime` for timestamps, age, DOB validation |
| Standard library | `json`, `os`, `re`, `math`, `shutil`, `datetime`, `unittest` |

## 13. Example Workflow

1. Run `python main.py`.
2. Choose **1** and register `S001 - Ada Lovelace - SS 2A - F - 2008-03-15`.
3. Choose **6**, select `S001`, enter scores `90 80 70 60 50 70` (average 70, grade A).
4. Choose **7** to correct CSC301 to `95`.
5. Choose **8** to view Ada's report card (total, average, grade, class position, timestamps).
6. Register more students and record their scores, then choose **10** to see the ranking and **11** for class statistics.
7. Choose **12** and answer `y` to save the academic report in `generated_reports/`.
8. Choose **13** to exit. Run the program again: all records are still there.

## 14. Known Limitations

- Single-user, local application: no login or role-based access (the brief's "authorised personnel" is assumed to be whoever can run the program).
- The subject list is fixed in code and shared by all classes.
- One term/session only; scores are not kept per term or academic year.
- Student IDs cannot be changed after registration (delete and re-register instead).
- Dates must be entered as `YYYY-MM-DD`.
- Reports are plain text, with no PDF or Excel export.
- The JSON file is loaded fully into memory, which is fine for a school's class but not for very large datasets.

## 15. Future Improvement Possibilities

- User login and permissions for administrators and teachers.
- Per-class and per-term records; configurable subjects and grading scales.
- Weighted scores (continuous assessment plus exam).
- Export to CSV, Excel or PDF; import students from CSV.
- Graphical interface (Tkinter) or a web version.
- Charts for class performance.
- Automatic periodic backups of the database.

## 16. Author

| Field | Details |
|-------|---------|
| **Name** | Smart Samuel Oluwaseyi |
| **Matriculation / Student Number** | 24/sci01/195 |
| **Course** | Introduction to Python Programming |
| **Institution** | New Horizon |
| **Supervisor / Instructor** | `[INSTRUCTOR NAME]` |
| **Date** | November 13, 2026 |
| **GitHub** | N/A |
