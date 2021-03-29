import create_print_out
import sort_data
import create_gephi


def main() -> None:
    students = sort_data.get_students()
    for student in students.values():
        create_print_out.create_student_print_out(student)
    # create_print_out.create_student_comparison_print_out(
    #     list(students.values()))
    create_gephi.create_gefx(list(students.values()))


if __name__ == "__main__":
    main()
