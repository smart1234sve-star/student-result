"""Automated tests for the Student Result Management System.

Run from the project folder with:   python -m unittest discover -s tests -v
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import reports          # noqa: E402
import results          # noqa: E402
import storage          # noqa: E402
import student as student_module   # noqa: E402
import utils            # noqa: E402
from student import Student        # noqa: E402


def make_student(sid="S1", name="Ada Lovelace", scores=None):
    s = Student(sid, name, "SS 1", "Female", "2008-03-15")
    for subject, value in (scores or {}).items():
        results.set_score(s, subject, value)
    return s


def full_scores(value):
    return {subject: value for subject in results.SUBJECTS}


class ImportTests(unittest.TestCase):
    def test_all_modules_import(self):
        for name in ("utils", "results", "student", "storage", "reports", "main"):
            __import__(name)


class GradeTests(unittest.TestCase):
    def test_grade_boundaries(self):
        cases = {100: "A", 70: "A", 69.99: "B", 60: "B", 59.99: "C", 50: "C",
                 49.99: "D", 45: "D", 44.99: "F", 0: "F"}
        for average, grade in cases.items():
            self.assertEqual(results.assign_grade(average), grade, average)

    def test_total_and_average(self):
        scores = dict(zip(results.SUBJECTS, [80, 70, 60, 50, 40, 60]))
        self.assertEqual(results.calculate_total(scores), 360)
        self.assertEqual(results.calculate_average(scores), 60)
        self.assertEqual(results.compute_result(scores)["grade"], "B")

    def test_incomplete_has_no_result(self):
        scores = {"CSC301": 90}
        self.assertIsNone(results.calculate_total(scores))
        self.assertIsNone(results.compute_result(scores))

    def test_score_validation(self):
        for bad in ("-1", "101", "abc", "", "nan", "inf", "100.01"):
            self.assertFalse(results.validate_score(bad)[0], bad)
        self.assertEqual(results.validate_score("0"), (True, 0))
        self.assertEqual(results.validate_score("100"), (True, 100))
        self.assertEqual(results.validate_score("55.5"), (True, 55.5))

    def test_timestamps_set_on_entry_and_update(self):
        s = make_student()
        self.assertIsNone(s.results_entered)
        results.set_score(s, "CSC301", 50)
        self.assertIsNotNone(s.results_entered)
        self.assertIsNotNone(s.results_updated)


class ValidationTests(unittest.TestCase):
    def test_validators(self):
        self.assertFalse(utils.validate_student_id("  ")[0])
        self.assertFalse(utils.validate_student_id("a b")[0])
        self.assertEqual(utils.validate_student_id(" s001 "), (True, "S001"))
        self.assertFalse(utils.validate_name("Madonna")[0])
        self.assertFalse(utils.validate_name("J0hn Doe")[0])
        self.assertEqual(utils.validate_name("ada  lovelace"), (True, "Ada Lovelace"))
        self.assertEqual(utils.validate_gender("f"), (True, "Female"))
        self.assertFalse(utils.validate_gender("x")[0])
        self.assertFalse(utils.validate_dob("2008-02-30")[0])
        self.assertFalse(utils.validate_dob("15/03/2008")[0])
        self.assertFalse(utils.validate_dob("2999-01-01")[0])
        self.assertTrue(utils.validate_dob("2008-03-15")[0])


class StudentTests(unittest.TestCase):
    def test_duplicate_ids_rejected(self):
        students = {}
        student_module.add_student(students, make_student("S1"))
        with self.assertRaises(ValueError):
            student_module.add_student(students, make_student("S1", "Other Person"))

    def test_search_and_delete(self):
        students = {}
        student_module.add_student(students, make_student("S1", "Ada Lovelace"))
        student_module.add_student(students, make_student("S2", "Alan Turing"))
        self.assertEqual(len(student_module.search_students(students, "ada")), 1)
        self.assertEqual(len(student_module.search_students(students, "a")), 2)
        self.assertEqual(student_module.search_students(students, "s2")[0].name, "Alan Turing")
        self.assertEqual(student_module.search_students(students, "zzz"), [])
        student_module.delete_student(students, "s1")
        self.assertNotIn("S1", students)
        with self.assertRaises(KeyError):
            student_module.delete_student(students, "S1")

    def test_round_trip_dict(self):
        s = make_student("S1", scores=full_scores(75))
        clone = Student.from_dict(json.loads(json.dumps(s.to_dict())))
        self.assertEqual(clone.to_dict(), s.to_dict())
        self.assertIsNotNone(clone.results_entered)

    def test_from_dict_rejects_bad_data(self):
        bad = make_student().to_dict()
        bad["scores"]["ICT305"] = 150
        with self.assertRaises(ValueError):
            Student.from_dict(bad)


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.a = make_student("S1", "Ann Alpha", full_scores(80))
        self.b = make_student("S2", "Ben Beta", full_scores(80))
        self.c = make_student("S3", "Cy Gamma", full_scores(40))
        self.d = make_student("S4", "Di Delta", {"CSC301": 99})   # incomplete
        self.all = [self.a, self.b, self.c, self.d]

    def test_ranking_orders_ties_and_excludes_incomplete(self):
        ranking = reports.rank_students(self.all)
        self.assertEqual([(r, s.student_id) for r, s, _ in ranking],
                         [(1, "S1"), (1, "S2"), (3, "S3")])

    def test_statistics(self):
        stats = reports.class_statistics(self.all)
        self.assertEqual(stats["total_students"], 4)
        self.assertEqual(stats["incomplete_count"], 1)
        self.assertEqual(stats["highest"][0], 80)
        self.assertEqual(stats["lowest"][0], 40)
        self.assertEqual(stats["class_average"], 66.67)

    def test_statistics_with_no_complete_results(self):
        stats = reports.class_statistics([self.d])
        self.assertIsNone(stats["highest"])
        self.assertIn("N/A", reports.format_statistics(stats))

    def test_sorting(self):
        shuffled = [self.c, self.a, self.d, self.b]
        self.assertEqual([s.name for s in reports.sort_students(shuffled, "name")],
                         ["Ann Alpha", "Ben Beta", "Cy Gamma", "Di Delta"])
        self.assertEqual([s.student_id for s in reports.sort_students(shuffled, "id")],
                         ["S1", "S2", "S3", "S4"])

    def test_report_card_complete_and_incomplete(self):
        self.assertIn("Class Position", reports.format_report_card(self.a, self.all))
        card = reports.format_report_card(self.d, self.all)
        self.assertIn("INCOMPLETE", card)
        self.assertNotIn("Class Position", card)

    def test_save_report_creates_unique_files(self):
        with tempfile.TemporaryDirectory() as folder:
            target = os.path.join(folder, "new_dir")
            p1 = reports.save_report("hello", "academic report", target)
            p2 = reports.save_report("hello again", "academic report", target)
            self.assertNotEqual(p1, p2)
            self.assertTrue(os.path.isfile(p1) and os.path.isfile(p2))


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.mkdtemp()
        self.db = os.path.join(self.folder, "data", "students.json")

    def tearDown(self):
        shutil.rmtree(self.folder, ignore_errors=True)

    def test_creates_directory_and_file(self):
        students, notices = storage.load_students(self.db)
        self.assertTrue(os.path.isfile(self.db))
        self.assertEqual((students, notices), ({}, []))

    def test_persistence_round_trip(self):
        original = {"S1": make_student("S1", scores=full_scores(65))}
        storage.save_students(original, self.db)
        loaded, notices = storage.load_students(self.db)
        self.assertEqual(notices, [])
        self.assertEqual(loaded["S1"].to_dict(), original["S1"].to_dict())

    def test_empty_file(self):
        os.makedirs(os.path.dirname(self.db))
        open(self.db, "w").close()
        students, notices = storage.load_students(self.db)
        self.assertEqual(students, {})
        self.assertEqual(len(notices), 1)

    def test_corrupt_file_is_backed_up(self):
        os.makedirs(os.path.dirname(self.db))
        with open(self.db, "w") as handle:
            handle.write('{"students": [ {broken')
        students, notices = storage.load_students(self.db)
        self.assertEqual(students, {})
        backups = [f for f in os.listdir(os.path.dirname(self.db)) if ".bak-" in f]
        self.assertEqual(len(backups), 1)
        self.assertIn("corrupted", notices[0])

    def test_bad_records_skipped_but_original_preserved(self):
        good = make_student("S1").to_dict()
        payload = {"students": [good, {"student_id": "S2"}, good]}
        os.makedirs(os.path.dirname(self.db))
        with open(self.db, "w") as handle:
            json.dump(payload, handle)
        students, notices = storage.load_students(self.db)
        self.assertEqual(list(students), ["S1"])
        self.assertTrue(any(".bak-" in f for f in os.listdir(os.path.dirname(self.db))))
        self.assertIn("2 invalid", notices[0])

    def test_wrong_structure(self):
        os.makedirs(os.path.dirname(self.db))
        with open(self.db, "w") as handle:
            handle.write("[1, 2, 3]")
        students, _ = storage.load_students(self.db)
        self.assertEqual(students, {})


class EndToEndTests(unittest.TestCase):
    """Runs the real program in a throw-away copy of the project, feeding it keystrokes."""

    def setUp(self):
        self.folder = tempfile.mkdtemp()
        self.project = os.path.join(self.folder, "proj")
        shutil.copytree(ROOT, self.project, ignore=shutil.ignore_patterns(
            "__pycache__", "*.pyc", "students.json", "*.txt", ".git"))

    def tearDown(self):
        shutil.rmtree(self.folder, ignore_errors=True)

    def run_app(self, lines):
        proc = subprocess.run([sys.executable, "main.py"], cwd=self.project,
                              input="\n".join(lines) + "\n", capture_output=True,
                              text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("Traceback", proc.stdout + proc.stderr)
        return proc.stdout

    def db(self):
        with open(os.path.join(self.project, "data", "students.json"), encoding="utf-8") as h:
            return json.load(h)

    def test_full_session_and_persistence(self):
        out = self.run_app([
            "1", "s001", "ada lovelace", "ss 2a", "f", "2008-03-15", "",
            "1", "S001", "cancel", "",                       # duplicate ID, then cancel
            "1", "S002", "Alan Turing", "SS 2A", "M", "2007-06-23", "",
            "1", "S003", "Grace Hopper", "SS 2A", "F", "2008-12-09", "",
            "6", "S001", "90", "80", "70", "60", "50", "70", "",   # average 70 -> grade A
            "6", "S002", "100", "101", "-5", "abc", "40", "40", "40", "40", "40", "",
            "6", "S003", "55", "", "", "", "", "", "",       # incomplete (1 of 6)
            "2", "2", "",                                    # view all, sorted by name
            "3", "turing", "",                               # search
            "4", "S002", "", "", "", "", "",                 # update info, no changes
            "7", "S001", "1", "30", "0", "",                 # update CSC301 to 30
            "8", "S001", "n", "",                            # report card, do not save
            "9", "1", "",                                    # all results
            "10", "", "11", "", "99", "abc", "",             # ranking, stats, invalid menu
            "12", "n", "",                                   # academic report, do not save
            "5", "S003", "n", "",                            # decline deletion
            "13",
        ])
        for text in ("Student registered", "Score must be between 0 and 100",
                     "already registered", "Incomplete (1/6)", "Class Position",
                     "Invalid selection '99'", "Deletion cancelled", "GOODBYE"):
            self.assertIn(text, out)
        data = self.db()
        self.assertEqual([s["student_id"] for s in data["students"]], ["S001", "S002", "S003"])
        self.assertEqual(data["students"][0]["scores"]["CSC301"], 30)

        # Second run: records are reloaded; delete S003 and save a report.
        out2 = self.run_app(["2", "1", "", "5", "S003", "y", "", "12", "y", "", "13"])
        self.assertIn("Loaded 3 student record(s)", out2)
        self.assertEqual(len(self.db()["students"]), 2)
        reports_dir = os.path.join(self.project, "generated_reports")
        self.assertTrue(any(f.startswith("academic_report_") for f in os.listdir(reports_dir)))


    def test_eof_exits_cleanly(self):
        out = self.run_app([])
        self.assertIn("GOODBYE", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
