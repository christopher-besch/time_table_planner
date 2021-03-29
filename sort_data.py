#!/urs/bin/env python
from typing import ValuesView, cast, List, Dict, Tuple, Union, Optional, Set
import sys
import csv
from fuzzywuzzy import fuzz, process

import read_course_file
import read_time_table


# representing a single course from a file
# there might be multiple FileCourse objects for a single real course
# pretty much a simpler version of read_course_file.File
class FileCourse:
    def __init__(self, name: str, abbreviation: str, teacher: str, p_level: int):
        self.name = name
        self.abbreviation = abbreviation
        self.teacher = teacher
        self.p_level = p_level
        # internal label for this instance of this course
        self.fuzzy_label = f"{self.name} {self.abbreviation} {self.teacher}"

    def __repr__(self):
        return f"{self.name} {self.abbreviation} {self.teacher}"


# represent student with references to courses
# contains non-fuzzy info
class Student:
    def __init__(self, name: str, group: str):
        self.name = name
        # A or B
        self.group = group
        self.fuzzy_names: List[str] = []
        self.fuzzy_tutor_abbreviations: List[str] = []
        self.file_courses: List[FileCourse] = []
        # p_level == 0
        self.cover_file_courses: List[FileCourse] = []
        # sorted by p-level
        self.p_file_courses: Dict[int, Optional[FileCourse]] = {
            1: None,
            2: None,
            3: None,
            4: None,
            5: None,
        }
        # same as before but this time not fuzzy
        self.cover_courses: List[read_time_table.Course] = []
        self.p_courses: Dict[int, Optional[read_time_table.Course]] = {
            1: None,
            2: None,
            3: None,
            4: None,
            5: None,
        }
        self.tutor = ""
        self.tutor_abbreviation = ""
        self.amount_courses = -1
        self.weekly_periods = -1

    def get_all_courses(self) -> List[read_time_table.Course]:
        courses: List[read_time_table.Course] = []
        for cover_course in self.cover_courses:
            courses.append(cover_course)
        for p_course in self.p_courses.values():
            courses.append(cast("read_time_table.Course", p_course))
        return courses

    def sort_courses(self) -> None:
        self.file_courses.sort(key=lambda course: course.p_level)
        # sort courses
        for course in self.file_courses:
            # not a p course
            if course.p_level == 0:
                self.cover_file_courses.append(course)
            # is a p course
            else:
                # when this spot is already taken, something is wrong
                if self.p_file_courses[course.p_level] is not None:
                    print(f"Critical: Doubling p_level for {self}")
                    sys.exit(1)
                self.p_file_courses[course.p_level] = course

        # check for missing courses
        if not 3 <= len(self.cover_file_courses) <= 7:
            print(f"Critical: Amount of cover courses is invalid for {self}")
            sys.exit(1)
        for p_level in self.p_file_courses:
            if self.p_file_courses[p_level] is None:
                print(f"Critical: Can't find P{p_level} for {self}")
                sys.exit(1)

    def count_stuff(self) -> None:
        self.amount_courses = 0
        self.weekly_periods = 0
        for course in self.cover_courses:
            self.amount_courses += 1
            self.weekly_periods += len(course.time_slots)
        for course in cast("ValuesView[read_time_table.Course]", self.p_courses.values()):
            self.amount_courses += 1
            self.weekly_periods += len(course.time_slots)

    def __repr__(self):
        return f"{self.name} tutor: {', '.join(self.fuzzy_tutor_abbreviations)} group: {self.group} courses:\n" + "\n".join([str(course) for course in self.file_courses])


# print each warning only once
printed_warnings: List[str] = []


def print_warning(warning: str) -> None:
    global print_warning
    if warning not in printed_warnings:
        printed_warnings.append(warning)
        print(warning)


# get template objects for students
# key: non-fuzzy student name, value: Student object
def get_student_templates() -> Dict[str, Student]:
    students: Dict[str, Student] = {}
    with open("files/students.csv", "r", newline="", encoding="utf-8") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=";", quotechar='"')
        for row in csv_reader:
            students[row[1]] = (Student(row[1], row[0]))
    return students


# e.g.: get best matching student key for this student name
def get_match(query: str, collection: List[str]) -> str:
    # perfect match
    if collection.count(query) == 1:
        return query
    if collection.count(query) > 1:
        print(f"Critical: '{query} existent in collection more than once.")
        sys.exit(1)
    matches = process.extract(query, collection, limit=2)
    best_matches = [match for match in matches if match[1] >= 80]

    # perform post processing and checks
    if len(best_matches) > 1:
        print_warning(
            f"Warning: multiple matches for '{query}': {best_matches}")

    if len(best_matches) == 0:
        print(
            f"Critical: Can't find sufficient match for '{query}': {matches}")
        sys.exit(1)

    if abs(matches[0][1] - matches[1][1]) < 5:
        # calculate token set ratio for each match
        set_matches: List[Tuple[str, int, int]] = [
            (match[0], match[1], fuzz.token_set_ratio(query, match[0])) for match in matches]
        print_warning(
            f"Warning: using token set ratio to determine best match for '{query}': {set_matches}")
        best_match = sorted(
            set_matches, key=lambda match: match[2], reverse=True)[0]
        if abs(set_matches[0][2] - set_matches[1][2]) < 5 or best_match[2] < 80:
            print("Critical: Can't determine best match with token set ratio.")
            sys.exit(1)
    else:
        best_match = best_matches[0]
    return best_match[0]


# add course date to all students from one file
def load_students(file: read_course_file.File, student_templates: Dict[str, Student]) -> Dict[str, Student]:
    for student in file.students:
        match = get_match(student.name, list(student_templates.keys()))
        # store data
        student_templates[match].file_courses.append(
            FileCourse(file.course_name, file.course_abbreviation, file.teacher, student.p_level))
        student_templates[match].fuzzy_tutor_abbreviations.append(
            student.tutor_abbreviation)
        student_templates[match].fuzzy_names.append(student.name)
        # check group
        if student_templates[match].group != file.group:
            print(f"Critical: Group mismatch found for {student}.")
            sys.exit(1)

    return student_templates


# key: teacher abbreviation, value: full teacher name
def get_teachers(courses: List[read_time_table.Course]) -> Dict[str, str]:
    teachers: Dict[str, str] = {}
    for course in courses:
        teacher_abbreviation = course.teacher_abbreviation
        if teacher_abbreviation != "" and teacher_abbreviation not in teachers:
            teachers[teacher_abbreviation] = course.teacher
    return teachers


def get_fuzzy_tutor(string: str) -> str:
    aliases = {
        "Kal": "KAI",
        "sT": "ST",
        "st": "ST",
        "stü": "STÜ",
        "sTÜ": "STÜ",
        "SA": "GA",
        "Su": "GU",
        "su": "GU",
        "sST": "ST",
        "SU": "GU",
        "bD": "DD",
        "stP": "ST",
        "STP": "ST",
        "sTÜü": "STÜ",
        "stüu": "STÜ",
        "srü": "STÜ",
        "sSTÜü": "STÜ",
        "sTtüÜ": "STÜ",
        "u": "GU",
        "Kar": "KAI",
        "stÜ": "STÜ",
        "kal": "KAI"
    }
    if string in aliases:
        string = aliases[string]
    return string


# key: non-fuzzy student name, value: Student object
def get_students() -> Dict[str, Student]:
    # load files
    replacements = read_course_file.get_replacements()
    students = get_student_templates()
    for i in range(1, 63):
        # A
        file_path = f"files/12_A/pg_{f'000{i}'[-4:]}.txt"
        file = read_course_file.parse_file(file_path, replacements)
        students = load_students(file, students)
        # B
        file_path = f"files/12_B/pg_{f'000{i}'[-4:]}.txt"
        file = read_course_file.parse_file(file_path, replacements)
        students = load_students(file, students)

    # load time table
    courses = read_time_table.get_courses()
    teachers = get_teachers(list(courses.values()))

    # sort data for each student
    for student in students.values():
        student.sort_courses()
        # add updated, non-fuzzy courses
        for p, p_file_course in student.p_file_courses.items():
            student.p_courses[p] = courses[cast(
                "FileCourse", p_file_course).fuzzy_label]
        for cover_file_course in student.cover_file_courses:
            student.cover_courses.append(
                courses[cover_file_course.fuzzy_label])
        # add tutor
        found_tutor_abbreviations: List[str] = []
        for fuzzy_tutor_abbreviation in student.fuzzy_tutor_abbreviations:
            fuzzy_tutor_abbreviation = get_fuzzy_tutor(
                fuzzy_tutor_abbreviation)
            found_tutor_abbreviations.append(
                get_match(fuzzy_tutor_abbreviation, list(teachers.keys())))

        # get tutor with most matches
        found_tutor_abbreviations.sort()
        student.tutor_abbreviation = max(
            set(found_tutor_abbreviations), key=found_tutor_abbreviations.count)
        student.tutor = teachers[student.tutor_abbreviation]

        if found_tutor_abbreviations.count(student.tutor_abbreviation) != len(found_tutor_abbreviations):
            print(
                f"Warning: not all found tutors are being used {found_tutor_abbreviations} (using {student.tutor_abbreviation})")
        # count stuff
        student.count_stuff()

    return students
