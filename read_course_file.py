"""
parse all the data from a single file into a File object
no data interpretation
"""

from typing import List, Dict, Optional, Tuple, Union
import sys
import re
import csv


# represent a single student line in from a file
class Student:
    def __init__(self, name: str, tutor_abbreviation: str, p_level: int):
        self.name = name
        self.tutor_abbreviation = tutor_abbreviation
        self.p_level = p_level
        self.check_integrity()

    def check_integrity(self) -> None:
        if self.name == "":
            print("Critical: Student name empty.")
            sys.exit(1)
        if self.tutor_abbreviation == "":
            print("Critical: Tutor name empty.")
            sys.exit(1)
        if not 0 <= self.p_level <= 5:
            print("Critical: Invalid P-level.")
            sys.exit(1)

    def is_lk(self) -> bool:
        return 1 <= self.p_level <= 3

    def __repr__(self) -> str:
        return f"{self.name} {self.tutor_abbreviation} {self.p_level}"


# contains all the interesing information from a single file
class File:
    raw = ""
    course_name = ""
    course_abbreviation = ""
    teacher = ""
    group = ""
    students: List[Student]

    def __init__(self, raw):
        self.raw = raw

    # is this object ok to be used
    def check_integrity(self) -> None:
        if self.raw == "":
            print("Critical: Raw is empty.")
            sys.exit(1)
        if self.course_name == "":
            print("Critical: Course name empty.")
            sys.exit(1)
        if self.course_abbreviation == "":
            print("Critical: Course abbreviation empty.")
            sys.exit(1)
        if self.teacher == "":
            print("Critical: Teacher empty.")
            sys.exit(1)
        if self.group != "A" and self.group != "B":
            print("Critical: Course group broken.")
            sys.exit(1)
        for student in self.students:
            student.check_integrity()
        if any([student.is_lk() for student in self.students]) and not all([student.is_lk() for student in self.students]):
            print("Critical: Some but not all students have this as one of their LKs.")
            sys.exit(1)

    def __repr__(self):
        students_repr = "\n".join(str(student) for student in self.students)
        return f"""{self.raw}\n
--------------------\n\n
course: {self.course_name} {self.course_abbreviation}\n\n
teacher: {self.teacher}\n\n
group: {self.group}\n\n
students: {students_repr}"""


# load low level replacements from file
def get_replacements() -> Dict[str, str]:
    corrections: Dict[str, str] = {}
    with open("files/replace_list.csv", "r", encoding="utf-8", newline="") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=";", quotechar='"')
        for row in csv_reader:
            # escape line breaks
            corrections[row[0].replace("\\n", "\n")
                        ] = row[1].replace("\\n", "\n")
    return corrections


def apply_replacements(text: str, replacements: Dict[str, str]) -> str:
    for key, value in replacements.items():
        text = text.replace(key, value)
    return text


def read_file(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as file:
        raw_text = file.read()

    # remove empty lines
    lines = [line for line in raw_text.split("\n") if line.strip() != ""]
    return "\n".join(lines)


# find regex pattern
def get_element(text: str, pattern: str) -> List[str]:
    # todo: shouldn't be iter
    matches = list(re.finditer(pattern, text, re.MULTILINE))
    if len(matches) != 0:
        return list(matches[0].groups())
    else:
        print(f"Critical: Can't find \"{pattern}\":\n{text}")
        sys.exit(1)


def get_p_level(input_str: str) -> int:
    character = input_str[-1]
    aliases = {
        "A": "4",
        "i": "1",
        "ı": "1",
        "I": "1",
        "S": "5",
        "a": "4",
        "s": "5",
        "t": "1"
    }
    if character in aliases:
        character = aliases[character]
    return int(character)


# parse all students from a single file
def get_students(text: str) -> List[Student]:
    # everything before name tag can't be used
    name_line_idx: Optional[int] = None
    for line_idx, line in enumerate(text.split("\n")):
        if "name" in line.lower():
            name_line_idx = line_idx
            break
    if name_line_idx is None:
        print(f"Critical: Can't find Name tag in: {text}")
        sys.exit(1)
    cut_text = "\n".join(text.split("\n")[name_line_idx + 1:])

    # find with regex
    matches = re.finditer(
        r"  +(\S{3,}(?:\S{2,}|(?: \S| {,15}\S{4}))+) +(?:(\w*) *([Pp]+\S)|(\w*))", cut_text)
    students: List[Student] = []
    for match in matches:
        groups = match.groups()
        # when this course is a p-course
        if groups[3] is None:
            students.append(
                Student(groups[0], groups[1], get_p_level(groups[2])))
        # when not a p-course
        else:
            students.append(Student(groups[0], groups[3], 0))
    return students


# load file from disk into File object
def parse_file(file_path: str, replacements: Dict[str, str]) -> File:
    text = read_file(file_path)
    text = apply_replacements(text, replacements)
    file = File(text)

    file.course_abbreviation, file.course_name = get_element(
        file.raw, r"Kursliste(?:\n.*\n)?\n?\s*?([\w\d]{2,4}) *- *(.+?\S)(?:   +| *?\n)")
    file.teacher = get_element(
        file.raw, r"Kursleiter:(?:\n.*\n)?\n?\s*?(\S.*?\S)(?:   +| *?\n)")[0]
    file.group = get_element(file.raw, r"GRUPPE *([A-Z])")[0]
    file.students = get_students(text)

    file.check_integrity()

    return file
