from read_time_table import load_time_table
from typing import cast, List, Dict, Tuple, Optional
import sys
from datetime import date

import sort_data
import create_print_out
import read_time_table


# representing all the information of a single student shown in the gephi graph
class GraphStudent:
    def __init__(self, id: int, name: str, courses: List[str], tutor: str, amount_courses: int, weekly_periods: int):
        self.id = id
        self.label = name
        # course labels
        self.courses = courses
        # key: connected student id, value: amount of connected periods
        self.connected_students: Dict[int, int] = {}
        # attributes
        self.tutor = tutor
        self.amount_courses = amount_courses
        self.weekly_periods = weekly_periods

    def __repr__(self):
        return f"{self.id}: {self.label}"


class GraphCourse:
    def __init__(self, id: int, label: str, students: List[str], teacher: str, weekly_periods: int):
        self.id = id
        self.label = label
        # student names
        self.students = students
        # key: connected course id, value: amount of students with both courses
        self.connected_courses: Dict[int, int] = {}
        # attributes
        self.teacher = teacher
        self.amount_students = len(self.students)
        self.weekly_periods = weekly_periods

    def __repr__(self):
        return f"{self.id}: {self.label}"


class Edge:
    def __init__(self, id: int, source: int, target: int, weight: int):
        self.id = id
        self.source = source
        self.target = target
        self.weight = weight

    def __repr___(self):
        return f"{self.id}: {self.source}-{self.target} {self.weight}"


def add_or_increment(dict: Dict[int, int], new_key, add_value) -> Dict[int, int]:
    if new_key in dict.keys():
        dict[new_key] += add_value
    else:
        dict[new_key] = add_value
    return dict


# todo: a lot of code duplication coming up, too bad
def get_graph_students(students: List[sort_data.Student], use_period_amount: bool) -> List[GraphStudent]:
    graph_students: List[GraphStudent] = []
    for id, student in enumerate(students):
        graph_student = GraphStudent(
            id,
            student.name,
            [course.full_label for course in student.get_all_courses()],
            f"{student.tutor} ({student.tutor_abbreviation})",
            student.amount_courses,
            student.weekly_periods
        )
        # add connections
        for course in student.get_all_courses():
            # find all other students in this course
            for other_student in graph_students:
                # are connected?
                if course.full_label in other_student.courses:
                    if use_period_amount:
                        add_amount = len(course.time_slots)
                    else:
                        add_amount = 1
                    add_or_increment(
                        graph_student.connected_students, other_student.id, add_amount)
        graph_students.append(graph_student)
    return graph_students


def get_graph_courses(courses: List[read_time_table.Course]) -> List[GraphCourse]:
    graph_courses: List[GraphCourse] = []
    for id, course in enumerate(courses):
        graph_course = GraphCourse(
            id,
            course.full_label,
            [student.name for student in course.students],
            f"{course.teacher} ({course.teacher_abbreviation})",
            len(course.time_slots)
        )
        # add connections
        for student in course.students:
            # find all other courses with this student
            for other_course in graph_courses:
                # are connected?
                if student.name in other_course.students:
                    add_or_increment(
                        graph_course.connected_courses, other_course.id, 1)
        graph_courses.append(graph_course)
    return graph_courses


# get all connections between all students
def get_student_edges(graph_students: List[GraphStudent]) -> List[Edge]:
    edges: List[Edge] = []
    for graph_student in graph_students:
        for other_id, weight in graph_student.connected_students.items():
            edges.append(Edge(len(edges), graph_student.id, other_id, weight))
    return edges


# get all connections between all courses
def get_course_edges(graph_courses: List[GraphCourse]) -> List[Edge]:
    edges: List[Edge] = []
    for graph_course in graph_courses:
        for other_id, weight in graph_course.connected_courses.items():
            edges.append(Edge(len(edges), graph_course.id, other_id, weight))
    return edges


def create_gefx(students: List[sort_data.Student]) -> None:
    today = date.today().strftime("%Y-%m-%d")

    # with periods amount
    graph_students = get_graph_students(students, True)
    student_edges = get_student_edges(graph_students)
    create_print_out.write_template(
        "files/gephi_students_template.gexf", "out/gephi/students_network_periods_amount.gexf",
        today=today, students=graph_students, edges=student_edges)
    # with courses amount
    graph_students = get_graph_students(students, False)
    student_edges = get_student_edges(graph_students)
    create_print_out.write_template(
        "files/gephi_students_template.gexf", "out/gephi/students_network_courses_amount.gexf",
        today=today, students=graph_students, edges=student_edges)

    courses: List[read_time_table.Course] = []
    for student in students:
        for course in student.get_all_courses():
            course.students.append(student)
            if course not in courses:
                courses.append(course)

    graph_courses = get_graph_courses(courses)
    course_edges = get_course_edges(graph_courses)
    create_print_out.write_template(
        "files/gephi_courses_template.gexf", "out/gephi/courses_network.gexf",
        today=today, courses=graph_courses, edges=course_edges)
