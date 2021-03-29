# {{ name }}

(Alias: {{ ", ".join(aliases) }})

|                        |                                       |
| :--------------------- | :------------------------------------ |
| Tutor                  | {{ tutor }} ({{ tutor_abbreviation}}) |
| Group                  | {{ group }}                           |
| Amount of Courses      | {{ amount_courses }}                  |
| Total Periods per Week | {{ weekly_periods }}                  |

## Time Table

|     |      Time       | Monday                         | Tuesday | Wednesday | Thursday | Friday |
| :-: | :-------------: | :----------------------------- | :------ | :-------- | :------- | :----- |
|  1  | 07:50 <br/>08:35 | {{ time_table_print_out[1] }}  |
|  2  | 08:40 <br/>09:25 | {{ time_table_print_out[2] }}  |
|  3  | 09:45 <br/>10:30 | {{ time_table_print_out[3] }}  |
|  4  | 10:35 <br/>11:20 | {{ time_table_print_out[4] }}  |
|  5  | 11:40 <br/>12:35 | {{ time_table_print_out[5] }}  |
|  6  | 12:30 <br/>13:15 | {{ time_table_print_out[6] }}  |
|  7  | 13:40 <br/>14:25 | {{ time_table_print_out[7] }}  |
|  8  | 14:25 <br/>15:10 | {{ time_table_print_out[8] }}  |
|  9  | 15:10 <br/>15:55 | {{ time_table_print_out[9] }}  |
| 10  | 15:55 <br/>16:40 | {{ time_table_print_out[10] }} |

## Courses

|                                                | Name                                                                              | Teacher                                                                          | Periods per Week                           |
| :--------------------------------------------- | :-------------------------------------------------------------------------------- | :------------------------------------------------------------------------------- | :----------------------------------------- |
{% for p_level in range(1, 6) %}| P{{ p_level }} | {{ p_courses[p_level].full_label }} ({{ p_courses[p_level].time_table_subject }}) | {{ p_courses[p_level].teacher }} ({{ p_courses[p_level].teacher_abbreviation }}) | {{ p_courses[p_level].time_slots|length }} |
{% endfor %}{% for cover_course in cover_courses %}| | {{ cover_course.full_label }} ({{ cover_course.time_table_subject }}) | {{ cover_course.teacher }} ({{ cover_course.teacher_abbreviation }}) | {{ cover_course.time_slots|length }} |
{% endfor %}

Courses that take place every other week are not flagged, which may lead to multiple courses appearing in the same cell of the time table.
Because of that some "Periods per Week" and the "Total Periods per Week" value may be slightly too high.
Since this happens with every student, these values can still be used to compare different students with each other.

