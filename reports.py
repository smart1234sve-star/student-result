"""Report generation: tables, report cards, rankings, class statistics and text reports."""

import os
from datetime import datetime

from results import GRADE_BANDS, SUBJECTS, compute_result, count_recorded, is_complete
from utils import LINE_WIDTH, separator, timestamp, truncate

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(BASE_DIR, "generated_reports")


# ------------------------------------------------------------------ helpers
def sort_students(students, mode="registered"):
    """Return a list of students ordered by 'name', 'id' or 'registered'."""
    students = list(students)
    if mode == "name":
        return sorted(students, key=lambda s: (s.name.lower(), s.student_id))
    if mode == "id":
        return sorted(students, key=lambda s: s.student_id)
    return students


def rank_students(students):
    """Rank students with complete results by average (highest first).

    Returns a list of (rank, student, result). Students with equal averages
    share a rank (1, 2, 2, 4 ...). Incomplete students are excluded.
    """
    scored = []
    for student in students:
        result = compute_result(student.scores)
        if result is not None:
            scored.append((student, result))
    scored.sort(key=lambda pair: (-pair[1]["average"], pair[0].name.lower()))

    ranking = []
    previous_average = None
    rank = 0
    for position, (student, result) in enumerate(scored, start=1):
        if result["average"] != previous_average:
            rank = position
            previous_average = result["average"]
        ranking.append((rank, student, result))
    return ranking


def class_statistics(students):
    """Summary figures for the class (based on complete results only)."""
    ranking = rank_students(students)
    stats = {
        "total_students": len(students),
        "complete_count": len(ranking),
        "incomplete_count": len(students) - len(ranking),
        "highest": None,
        "lowest": None,
        "class_average": None,
        "grade_counts": {grade: 0 for _, grade, _ in GRADE_BANDS},
    }
    if ranking:
        averages = [result["average"] for _, _, result in ranking]
        stats["highest"] = (ranking[0][2]["average"], ranking[0][1])
        stats["lowest"] = (ranking[-1][2]["average"], ranking[-1][1])
        stats["class_average"] = round(sum(averages) / len(averages), 2)
        for _, _, result in ranking:
            stats["grade_counts"][result["grade"]] += 1
    return stats


# ------------------------------------------------------------------- tables
def format_students_table(students):
    """Table of student details."""
    if not students:
        return "No students to display."
    lines = [f"{'No.':<4}{'Student ID':<14}{'Full Name':<28}{'Class':<10}{'Gender':<8}{'Date of Birth':<12}",
             separator("-")]
    for number, s in enumerate(students, start=1):
        lines.append(f"{number:<4}{truncate(s.student_id, 13):<14}{truncate(s.name, 27):<28}"
                     f"{truncate(s.class_name, 9):<10}{s.gender:<8}{s.date_of_birth:<12}")
    lines.append(separator("-"))
    lines.append(f"Total: {len(students)} student(s)")
    return "\n".join(lines)


def format_results_table(students):
    """Every student with total, average and grade (incomplete ones are marked)."""
    if not students:
        return "No students to display."
    lines = [f"{'Student ID':<14}{'Full Name':<28}{'Total':>8}{'Average':>10}{'Grade':>7}  Status",
             separator("-")]
    for s in students:
        result = compute_result(s.scores)
        if result:
            lines.append(f"{truncate(s.student_id, 13):<14}{truncate(s.name, 27):<28}"
                         f"{result['total']:>8.2f}{result['average']:>10.2f}{result['grade']:>7}  Complete")
        else:
            recorded = count_recorded(s.scores)
            lines.append(f"{truncate(s.student_id, 13):<14}{truncate(s.name, 27):<28}"
                         f"{'-':>8}{'-':>10}{'-':>7}  Incomplete ({recorded}/{len(SUBJECTS)})")
    lines.append(separator("-"))
    return "\n".join(lines)


def format_ranking_table(students):
    """Ranking of students with complete results, highest average first."""
    ranking = rank_students(students)
    if not ranking:
        return "No students have complete results yet, so no ranking is available."
    lines = [f"{'Rank':<6}{'Student ID':<14}{'Full Name':<28}{'Total':>8}{'Average':>10}{'Grade':>7}",
             separator("-")]
    for rank, s, result in ranking:
        lines.append(f"{rank:<6}{truncate(s.student_id, 13):<14}{truncate(s.name, 27):<28}"
                     f"{result['total']:>8.2f}{result['average']:>10.2f}{result['grade']:>7}")
    lines.append(separator("-"))
    excluded = len(students) - len(ranking)
    if excluded:
        lines.append(f"Note: {excluded} student(s) with incomplete results are not ranked.")
    return "\n".join(lines)


def format_statistics(stats):
    """Class statistics block."""
    def describe(entry):
        if entry is None:
            return "N/A"
        average, student = entry
        return f"{average:.2f}  ({student.name})"

    average = "N/A" if stats["class_average"] is None else f"{stats['class_average']:.2f}"
    lines = [
        f"Total registered students      : {stats['total_students']}",
        f"Students with complete results : {stats['complete_count']}",
        f"Students with incomplete results: {stats['incomplete_count']}",
        f"Highest average score          : {describe(stats['highest'])}",
        f"Lowest average score           : {describe(stats['lowest'])}",
        f"Overall class average          : {average}",
        "",
        "Grade distribution:",
    ]
    for _, grade, remark in GRADE_BANDS:
        lines.append(f"  Grade {grade} ({remark:<9}): {stats['grade_counts'][grade]}")
    return "\n".join(lines)


# -------------------------------------------------------------- report card
def format_report_card(student, all_students):
    """Individual report card for one student."""
    result = compute_result(student.scores)
    lines = [
        separator("="),
        "STUDENT REPORT CARD".center(LINE_WIDTH),
        separator("="),
        f"Student ID    : {student.student_id}",
        f"Full Name     : {student.name}",
        f"Class/Form    : {student.class_name}",
        f"Gender        : {student.gender}",
        f"Date of Birth : {student.date_of_birth} (age {student.age})",
        separator("-"),
        f"{'Subject':<28}{'Score':>10}",
        separator("-"),
    ]
    for subject in SUBJECTS:
        score = student.scores[subject]
        shown = "Not recorded" if score is None else f"{score:.2f}"
        lines.append(f"{subject:<28}{shown:>12}")
    lines.append(separator("-"))

    if result:
        position = next(rank for rank, s, _ in rank_students(all_students) if s is student)
        ranked_total = len(rank_students(all_students))
        lines += [
            f"{'Total Score':<28}{result['total']:>12.2f}",
            f"{'Average Score':<28}{result['average']:>12.2f}",
            f"{'Grade':<28}{result['grade']:>12}",
            f"{'Remark':<28}{result['remark']:>12}",
            f"{'Class Position':<28}{f'{position} of {ranked_total}':>12}",
        ]
    else:
        recorded = count_recorded(student.scores)
        lines += [
            f"Status: INCOMPLETE - {recorded} of {len(SUBJECTS)} subjects recorded.",
            "Total, average, grade and class position are unavailable until all",
            "subject scores have been recorded.",
        ]
    lines.append(separator("-"))
    lines.append(f"Results first entered : {student.results_entered or 'N/A'}")
    lines.append(f"Results last updated  : {student.results_updated or 'N/A'}")
    lines.append(f"Report generated      : {timestamp()}")
    lines.append(separator("="))
    return "\n".join(lines)


# ----------------------------------------------------------- academic report
def format_academic_report(students):
    """Full text-based academic report for the whole class."""
    stats = class_statistics(students)
    ordered = sort_students(students, "name")
    incomplete = [s for s in ordered if not is_complete(s.scores)]
    parts = [
        separator("="),
        "STUDENT RESULT MANAGEMENT SYSTEM".center(LINE_WIDTH),
        "ACADEMIC REPORT".center(LINE_WIDTH),
        separator("="),
        f"Generated: {timestamp()}",
        f"Subjects : {', '.join(SUBJECTS)}",
        "",
        "SECTION 1: CLASS STATISTICS",
        separator("-"),
        format_statistics(stats),
        "",
        "SECTION 2: STUDENT RANKING (highest average first)",
        separator("-"),
        format_ranking_table(students),
        "",
        "SECTION 3: ALL STUDENT RESULTS (alphabetical by name)",
        separator("-"),
        format_results_table(ordered),
    ]
    if incomplete:
        parts += ["", "SECTION 4: STUDENTS WITH INCOMPLETE RESULTS", separator("-")]
        for s in incomplete:
            missing = [sub for sub in SUBJECTS if s.scores[sub] is None]
            parts.append(f"{s.student_id} - {s.name}: missing {', '.join(missing)}")
    parts += ["", separator("="), "END OF REPORT".center(LINE_WIDTH), separator("=")]
    return "\n".join(parts)


def save_report(text, prefix, reports_dir=REPORTS_DIR):
    """Save report text to generated_reports/<prefix>_<timestamp>.txt and return the path."""
    os.makedirs(reports_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_prefix = "".join(c if c.isalnum() or c in "-_" else "_" for c in prefix)
    path = os.path.join(reports_dir, f"{safe_prefix}_{stamp}.txt")
    counter = 1
    while os.path.exists(path):          # never overwrite an earlier report
        counter += 1
        path = os.path.join(reports_dir, f"{safe_prefix}_{stamp}_{counter}.txt")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text + "\n")
    return path
