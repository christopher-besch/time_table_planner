from typing import cast, List, Dict, Tuple, ItemsView
import sys
from jinja2 import Template, StrictUndefined

import read_time_table
import sort_data


def write_template(in_file: str, out_file: str, **variables):
    with open(f"{in_file}", "r", encoding="utf-8") as file:
        template = Template(file.read(), undefined=StrictUndefined)
    out = template.render(**variables)
    with open(f"{out_file}", "w+", encoding="utf-8") as file:
        file.write(out)


def add_course_to_time_table(time_table: Dict[int, Dict[int, str]], course: read_time_table.Course) -> None:
    for time_slot in course.time_slots:
        rendered_time_slot = f"{course.full_label} </br>{time_slot.room}"
        if time_table[time_slot.period][time_slot.day] != "":
            sort_data.print_warning(
                f"Warning: conflicting time slots on {time_slot.day}. day {time_slot.period}. period: {time_table[time_slot.period][time_slot.day]} {rendered_time_slot}")
            time_table[time_slot.period][
                time_slot.day] += f" </br>-- or -- </br>{rendered_time_slot}"
        else:
            time_table[time_slot.period][time_slot.day] = rendered_time_slot


def create_student_print_out(student: sort_data.Student) -> None:
    # can be accessed with [period][day]
    time_table = {period_idx: {day_idx: "" for day_idx in range(
        5)} for period_idx in range(1, 11)}

    # go over all courses
    for course in student.cover_courses:
        add_course_to_time_table(time_table, course)

    for p_level, course in cast("ItemsView[int, read_time_table.Course]", student.p_courses.items()):
        add_course_to_time_table(time_table, course)

    time_table_print_out = {period_idx: " | ".join(
        time_slots.values()) for period_idx, time_slots in time_table.items()}

    write_template("files/student_print_out_template.md",
                   f"out/students/{student.name.replace(' ', '_').lower()}.md",
                   name=student.name,
                   aliases=set(student.fuzzy_names),
                   tutor=student.tutor,
                   tutor_abbreviation=student.tutor_abbreviation,
                   group=student.group,
                   amount_courses=student.amount_courses,
                   weekly_periods=student.weekly_periods,
                   time_table_print_out=time_table_print_out,
                   p_courses=student.p_courses,
                   cover_courses=student.cover_courses)


# todo: finish
def create_student_comparison_print_out(students: List[sort_data.Student]) -> None:
    students.sort(key=lambda student: student.weekly_periods)
    for student in students:
        print(f"{student.name}: {student.weekly_periods}")
