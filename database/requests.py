from sqlalchemy import exists, func, or_, select

from helpers import get_number_lesson, index_weekday
from models import Employee, StudentSchedule, StudentGroup
from models.employee_job_information import EmployeeJobInformation


list_days = ['0001-01-01', '0001-01-02', '0001-01-03', '0001-01-04', '0001-01-05', '0001-01-06', '0001-01-07', '0001-01-08', '0001-01-09', '0001-01-10', '0001-01-11', '0001-01-12', '0001-01-13', '0001-01-14']

# check group exists
async def check_group_exists(session, group: str):
    query = select(
        StudentGroup.id, StudentGroup.group_name
    ).where(
        func.lower(StudentGroup.group_name) == (group).lower()
        )
    
    result = await session.exec(query)
    group = result.one_or_none() 
    
    if not group: 
        return False, group
    return True, group

# check teacher exists
async def check_employee_exists(session, employee: str):
    """
    -1 - not found
    0 - one match found
    1 - multiple matches found
    """
    
    if '.' in employee or ' ' in employee:
        parts = employee.split()
        
        parts = [part.strip(' .') for part in parts if part.strip()]
        
        if len(parts) >= 2:
            surname = parts[0].lower()
            initials = ''.join(parts[1:]).lower()
            
            query = select(
                Employee.id, func.concat('<pre>', func.concat(Employee.surname, ' ', Employee.name, Employee.patronymic), '</pre>').label("employee_name")
            ).distinct(Employee.id).join(
                EmployeeJobInformation, EmployeeJobInformation.id_employee == Employee.id
            ).where(
                (func.lower(Employee.surname) == surname) & EmployeeJobInformation.employee.is_(True),
                or_(
                    func.lower(func.concat(Employee.name, Employee.patronymic)).contains(initials),
                    func.lower(func.concat(func.substr(Employee.name, 1, 1), func.substr(Employee.patronymic, 1, 1))) == initials
                ), (exists().where(StudentSchedule.id_teacher == Employee.id))
            )
            
            result = await session.exec(query)
            records = result.all()
            
            if len(records) == 1:
                return 0, records[0]
            elif len(records) > 1:
                return 1, records
            else:
                return -1, None
    
    query = select(
        Employee.id, func.concat('<pre>', Employee.surname, ' ', func.substr(Employee.name, 1, 1), func.substr(Employee.patronymic, 1, 1), '</pre>').label('employee_name')
    ).distinct(Employee.id).join(
        EmployeeJobInformation, EmployeeJobInformation.id_employee == Employee.id
    ).where(
        (func.lower(Employee.surname) == employee.lower().strip()) & (EmployeeJobInformation.employee.is_(True)) & (exists().where(StudentSchedule.id_teacher == Employee.id))
    )
    
    result = await session.exec(query)
    employee_records = result.all()
    
    if not employee_records:
        return -1, None
    elif len(employee_records) == 1:
        return 0, employee_records[0]
    else:
        return 1, employee_records

# formatting 1 pair
async def format_one_lesson(lesson, lesson_number: str) -> str:
    schedule_string = f"<b>{lesson_number} пара\n({str(lesson.time_lesson_starts)[:-3]}-{str(lesson.time_lesson_ends)[:-3]})</b>\n"
    
    if lesson.number_subgroup is not None:
        schedule_string += f"<i>{lesson.number_subgroup} подгруппа</i>\n"
    
    schedule_string += f"{lesson.lesson_type} - {lesson.subject}\n"
    teacher = lesson.employee if lesson.employee else ""
    schedule_string += f"Преподаватель: {teacher}\n"
    classroom = lesson.number_classroom if lesson.number_classroom else "Не указано"
    schedule_string += f"Ауд. {classroom}\n" + '\n'
    
    return schedule_string

# grouping schedule by time
async def group_lessons(lessons) -> dict:
    output_lessons = {}
    
    for lesson in lessons:
        time_ = f"{lesson.time_lesson_starts}-{lesson.time_lesson_ends}"
        if time_ not in output_lessons:
            output_lessons[time_] = []
        output_lessons[time_].append(lesson)
    
    return output_lessons

# schedule output formatting
async def format_lessons(lessons, lesson_number: str) -> str: 
    if len(lessons) == 1:
        return await format_one_lesson(lessons[0], lesson_number)
    else:
        # schedule string composition
        schedule_string = f"<b>{lesson_number} пара\n({lessons[0].time_lesson_starts.strftime('%H:%M')}-{lessons[0].time_lesson_ends.strftime('%H:%M')})</b>\n"
        
        for elem, lesson in enumerate(lessons):
            if elem > 0:
                schedule_string += "----\n"
            
            if lesson.number_subgroup is not None:
                schedule_string += f"<i>{lesson.number_subgroup} подгруппа</i>\n"
            
            schedule_string += f"{lesson.lesson_type} - {lesson.subject}\n"
            
            teacher = lesson.employee if lesson.employee else ""
            schedule_string += f"Преподаватель: {teacher}\n"
            classroom = lesson.number_classroom if lesson.number_classroom else "Не указано"
            schedule_string += f"Ауд. {classroom}\n\n"
        return schedule_string

# get actual schedule for specific date
async def get_schedule_by_date(session, current_day, group_id: int, group_name: str, type_weekday: str | None = None) -> str | None:
    query = select( 
        StudentSchedule.numerator_denominator, StudentSchedule.weekday,
        StudentSchedule.number_subgroup, StudentSchedule.time_lesson_starts,
        StudentSchedule.time_lesson_ends, StudentSchedule.subject,
        StudentSchedule.lesson_type, 
        func.concat(Employee.surname, ' ', Employee.name, ' ', Employee.patronymic).label('employee'),
        StudentSchedule.lesson_date, 
        StudentSchedule.number_classroom, StudentGroup.group_name
    ).join(
        StudentSchedule, StudentSchedule.id_group == StudentGroup.id
    ).join(
        Employee, Employee.id == StudentSchedule.id_teacher
    ).where(
        (StudentGroup.id == group_id) &
        (StudentSchedule.lesson_date == func.to_date(current_day, 'YYYY-MM-DD'))
    ).order_by(StudentSchedule.time_lesson_starts)
    
    schedule = await session.exec(query)
    lessons = schedule.all()
    
    if not lessons:
        return None
    
    lessons_by_time = await group_lessons(lessons)
    schedule_string = f"Расписание на {current_day}\nГруппа: {group_name}\n"
    
    for _, (_, time_lessons) in enumerate(lessons_by_time.items(), 1):
        lesson_number = await get_number_lesson(str(time_lessons[0].time_lesson_starts))
        schedule_string += await format_lessons(time_lessons, lesson_number)
    
    return schedule_string   

# main schedule function -> schedule string
async def get_group_schedule(session, current_day, group_id: int, group_name: str, current_date: str, type_weekday: str | None = None) -> str:
    if type_weekday is None: 
        type_weekday = await index_weekday()
    
    # get actual schedule, if not found - use planned schedule
    schedule = await get_schedule_by_date(session, current_date, group_id, group_name, type_weekday)
    if schedule is not None:
        return schedule
    
    # query to get planned schedule
    query = select(
        StudentSchedule.numerator_denominator, StudentSchedule.weekday,
        StudentSchedule.number_subgroup, StudentSchedule.time_lesson_starts,
        StudentSchedule.time_lesson_ends, StudentSchedule.subject,
        StudentSchedule.lesson_type, 
        func.concat(Employee.surname, ' ', Employee.name, ' ', Employee.patronymic).label('employee'),
        StudentSchedule.lesson_date, 
        StudentSchedule.number_classroom, StudentGroup.group_name
    ).join(
        StudentSchedule, StudentSchedule.id_group == StudentGroup.id
    ).join(
        Employee, Employee.id == StudentSchedule.id_teacher
    ).where(
        (StudentSchedule.numerator_denominator == str(type_weekday)) &
        (StudentSchedule.lesson_date.in_([func.to_date(date_str, 'YYYY-MM-DD') for date_str in list_days])) &
        (StudentSchedule.weekday == current_day) &
        ((StudentGroup.id == group_id))
    ).order_by(StudentSchedule.time_lesson_starts)
    
    result = await session.execute(query)
    lessons = result.all()
    
    if not lessons:
        return f"Группа: {group_name}\n{current_day} ({type_weekday})\nНет занятий"
    
    lessons_by_time = await group_lessons(lessons)
    
    schedule_string = f"Группа: {group_name}\n{current_day} ({type_weekday})\n"
    
    for _, (_, time_lessons) in enumerate(lessons_by_time.items(), 1):
        lesson_number = await get_number_lesson(str(time_lessons[0].time_lesson_starts))
        schedule_string += await format_lessons(time_lessons, lesson_number)
    
    return schedule_string

# get actual schedule for teacher
async def get_teacher_schedule_by_date(session, current_day, employee_id: int, current_date: str) -> str | None:
    query = select( 
        StudentSchedule.numerator_denominator, StudentSchedule.weekday,
        StudentSchedule.number_subgroup, StudentSchedule.time_lesson_starts,
        StudentSchedule.time_lesson_ends, StudentSchedule.subject,
        StudentSchedule.lesson_type, 
        func.concat(Employee.surname, ' ', Employee.name, ' ', Employee.patronymic).label('employee'),
        StudentSchedule.lesson_date, 
        StudentSchedule.number_classroom, StudentGroup.group_name
    ).join(
        StudentSchedule, StudentSchedule.id_group == StudentGroup.id
    ).join(
        Employee, Employee.id == StudentSchedule.id_teacher
    ).where(
        (Employee.id == employee_id) &
        (StudentSchedule.lesson_date == func.to_date(current_day, 'YYYY-MM-DD'))
    ).order_by(StudentSchedule.time_lesson_starts)
    
    schedule = await session.exec(query)
    lessons = schedule.all()
    
    if not lessons:
        return None
    
    lessons_by_time = await group_lessons(lessons)
    schedule_string = f"Расписание на {current_day}\n\n"
    
    for _, (_, time_lessons) in enumerate(lessons_by_time.items(), 1):
        lesson_number = await get_number_lesson(str(time_lessons[0].time_lesson_starts))
        schedule_string += await format_lessons(time_lessons, lesson_number)
    
    return schedule_string   

# get teacher schedule
async def get_teacher_schedule(session, current_day, employee_id: int, current_date: str, type_weekday: str | None = None) -> str:
    if type_weekday is None: 
        type_weekday = await index_weekday()
    
    # get actual schedule, if not found - use planned schedule
    schedule = await get_teacher_schedule_by_date(session, current_date, employee_id, type_weekday)
    if schedule is not None:
        return schedule
    
    # query to get planned schedule
    query = select(
        StudentSchedule.numerator_denominator, StudentSchedule.weekday,
        StudentSchedule.number_subgroup, StudentSchedule.time_lesson_starts,
        StudentSchedule.time_lesson_ends, StudentSchedule.subject,
        StudentSchedule.lesson_type, 
        func.concat(Employee.surname, ' ', Employee.name, ' ', Employee.patronymic).label('employee'),
        StudentSchedule.lesson_date, 
        StudentSchedule.number_classroom, StudentGroup.group_name
    ).join(
        StudentSchedule, StudentSchedule.id_group == StudentGroup.id
    ).join(
        Employee, Employee.id == StudentSchedule.id_teacher
    ).where(
        (StudentSchedule.numerator_denominator == str(type_weekday)) &
        (StudentSchedule.weekday == current_day) &
        (Employee.id == employee_id)
    ).order_by(StudentSchedule.time_lesson_starts)
    
    result = await session.execute(query)
    lessons = result.all()
    
    if not lessons:
        return f"Преподаватель: \n{current_day} ({type_weekday})\nНет занятий"
    
    lessons_by_time = await group_lessons(lessons)
    
    schedule_string = f"Преподаватель: \n{current_day} ({type_weekday})\n"
    
    for _, (_, time_lessons) in enumerate(lessons_by_time.items(), 1):
        lesson_number = await get_number_lesson(str(time_lessons[0].time_lesson_starts))
        schedule_string += await format_lessons(time_lessons, lesson_number)
    
    return schedule_string
