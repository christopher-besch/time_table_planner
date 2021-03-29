from typing import Any, cast, List, Tuple, Dict
import sys
import csv


# represent chronological and spacial location of a period
class TimeSpaceSlot:
    def __init__(self, day: int, period: int, room: str):
        self.day = day
        self.period = period
        self.room = room

    def __eq__(self, other: object):
        if not isinstance(other, TimeSpaceSlot):
            return NotImplemented
        return self.day == cast("TimeSpaceSlot", other).day and self.period == cast("TimeSpaceSlot", other).period

    def __repr__(self):
        days = ["Mon.", "Tues.", "Wed.", "Thurs.", "Fr."]
        return f"at {days[self.day]} {self.period}. period in {self.room}"


# represent single course
# all information in here is supposed to be clean, not fuzzy
class Course:
    def __init__(self, teacher_abbreviation: str, time_table_subject: str):
        self.teacher_abbreviation = teacher_abbreviation
        self.time_table_subject = time_table_subject
        self.time_slots: List[TimeSpaceSlot] = []
        # better label
        self.full_label = ""
        # full teacher name
        self.teacher = ""
        # containing names of students
        # todo: bad any
        self.students: List[Any] = []

    def add_time_slot(self, day: int, period: int, room: str):
        new_time_slot = TimeSpaceSlot(day, period, room)
        if new_time_slot in self.time_slots:
            print("Critical: doubled course in time table.")
            sys.exit(1)
        self.time_slots.append(new_time_slot)

    # courses without any periods are still supported but not integer in the sense of this method
    def check_integrity(self) -> None:
        if not 2 <= len(self.time_slots) <= 5:
            print(f"Invalid amount of time slots for {self}")
            sys.exit(1)

    def __repr__(self):
        return f"{self.time_table_subject} {self.teacher_abbreviation} ({self.full_label} {self.teacher}) in {', '.join([str(time_slot) for time_slot in self.time_slots])}"


# load new courses and add time slots to existing ones
def update_courses(course_identifiers: List[str],
                   day_idx: int, period_idx: int,
                   courses: Dict[str, Course]) -> None:
    for identifier in course_identifiers:
        identifier = identifier.strip()
        if identifier == "":
            continue
        teacher_abbreviation = identifier.split(" ")[0].upper()
        subject = identifier.split(" ")[1]
        room = identifier.split(" ")[2]

        course_name = f"{teacher_abbreviation} {subject}"
        # search for existing course
        if course_name not in courses:
            courses[course_name] = Course(teacher_abbreviation, subject)
        courses[course_name].add_time_slot(day_idx, period_idx, room)


# load all time table files
def load_time_table() -> Dict[str, Course]:
    time_table_courses: Dict[str, Course] = {}
    for day_idx in range(5):
        file_path = f"files/time_table/{day_idx}.csv"
        # parse file
        with open(file_path, "r", encoding="utf-8", newline="") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=";", quotechar='"')
            for period_idx, row in enumerate(csv_reader, start=1):
                update_courses(row, day_idx, period_idx, time_table_courses)
    # check for too many time slots
    for course in time_table_courses.values():
        course.check_integrity()
    # sort
    return {key: value for key, value in sorted(time_table_courses.items(), key=lambda item: item[0])}


# key: fuzzy label, value: non fuzzy Course object
def get_courses() -> Dict[str, Course]:
    time_table_courses = load_time_table()
    courses: Dict[str, Course] = {}
    with open("files/course_corrections.csv", "r", encoding="utf-8") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=";", quotechar='"')
        for row in csv_reader:
            if row[1] == "":
                # create course without periods
                # this wouldn't work with multiple representations in the fuzzy files of the same course
                this_course = Course("", row[3][:-1].upper())
            else:
                # get course from time table that corresponds with this line
                this_course = time_table_courses[row[1]]
            # add new info
            this_course.teacher = row[2]
            this_course.full_label = row[3]

            courses[row[0]] = this_course
    return courses
