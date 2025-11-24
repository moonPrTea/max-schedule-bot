import datetime
import re

from datetime import datetime, timedelta
from typing import Union
from maxapi import Dispatcher, F
from maxapi.context import MemoryContext
from maxapi.enums.parse_mode import ParseMode
from maxapi.types import BotStarted, Command, MessageCreated, MessageCallback
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import DBSessionMiddleware
from database import index_weekday, get_group_schedule, check_group_exists, check_employee_exists, get_teacher_schedule
from helpers import check_weekend, get_current_week_monday, get_next_week_monday
from helpers import ScheduleState, get_logger
from keyboards import start_keyboard, schedule_buttons, week_schedule_buttons, back_to_menu


logger = get_logger()

dp = Dispatcher()
dp.middleware(DBSessionMiddleware())

@dp.bot_started()
async def bot_started(event: BotStarted):
    await event.bot.send_message(
        chat_id=event.chat_id,
        text=(
        "Добро пожаловать в бот расписания!\n\n"
        "Я помогу вам найти расписание:\n"
        "\t• Академических групп\n"  
        "\t• Преподавателей\n\n"
        "Используйте кнопки ниже для навигации"
    ),
        attachments=[start_keyboard()]
    )

@dp.message_created(Command('start'))
async def bot_started(event: MessageCreated, context: MemoryContext):
    await context.set_state(None)
    await event.message.answer(
        text=(
        "Добро пожаловать в бот расписания!\n\n"
        "Я помогу вам найти расписание:\n"
        "\t• Академических групп\n"  
        "\t• Преподавателей\n\n"
        "Используйте кнопки ниже для навигации"
    ),
        attachments=[start_keyboard()]
    )
    
# start group schedule  
@dp.message_created(Command('group'))
@dp.message_callback(F.callback.payload == "group_schedule")
async def handle_group_schedule(event: Union[MessageCreated, MessageCallback], context: MemoryContext):
    await event.message.delete()
    
    user_data = await context.get_data()
    
    if user_data.get('group_name'):
        await event.message.delete()
        await event.bot.send_message(
        chat_id=event.chat.chat_id, 
        text=(
           f"Выбранная группа: {user_data.get('group_name')}\nДля смены группы введите ее название"
            ),
        attachments=[schedule_buttons()]
        )
        await context.set_state(ScheduleState.group_name)
        return 
    
    await event.bot.send_message(
        chat_id=event.chat.chat_id, 
        text=(
            "Введите название группы. Например, бТИИ-222"
        )
    )
    await context.set_state(ScheduleState.group_name)

# start teacher schedule  
@dp.message_created(Command('teacher'))
@dp.message_callback(F.callback.payload == "teacher_schedule")
async def handle_teacher_schedule(event: Union[MessageCreated, MessageCallback], context: MemoryContext):
    await event.message.delete()
    await event.bot.send_message(
        chat_id=event.chat.chat_id, 
        text=(
            "Введите ФИО преподавателя. Например, Иванов ИИ"
        )
    )
    
    await context.set_state(ScheduleState.teacher_name)

# input teacher
@dp.message_created(F.message.body.text, ScheduleState.teacher_name)
async def print_teacher_name(event: MessageCreated, context: MemoryContext, session: AsyncSession):
    group = event.message.body.text
    
    exists, employee = await check_employee_exists(session, group)
    if exists == -1:
        await event.message.answer(
            text=('Неизвестный преподаватель. Для указания преподавателя используйте команду <pre>/teacher</pre>'),
            parse_mode=ParseMode.HTML
        )
        return
    
    elif exists == 1:
        employees = list()
        print(employee)
        for emp in employee:
            id, name = emp
            employees.append(name)
        
        await event.message.answer(
            text=(f'Найдены преподаватели:\n'+ '\n'.join(employees)),
            parse_mode=ParseMode.HTML
        )
        return
    
    week_type = await index_weekday()
    id, name = employee
    await event.message.answer( 
        text=(
            f"Был выбран преподаватель : {name}.\nТекущая неделя: {week_type}"
        ),
        parse_mode=ParseMode.HTML,
        attachments=[schedule_buttons()]
    )
    
    await context.update_data(
        teacher_name=name,
        teacher_id = id,
        entity_type="teacher"
    )
    
    await context.set_state(ScheduleState.waiting_teacher_day)

# input group name
@dp.message_created(F.message.body.text, ScheduleState.group_name)
async def print_group_name(event: MessageCreated, context: MemoryContext, session: AsyncSession):
    group = event.message.body.text
    
    exists, groups = await check_group_exists(session, group)
    if exists == False:
        await event.message.answer(
            text=('Неизвестная группа. Для указания группы используйте команду <pre>/group</pre>'),
            parse_mode=ParseMode.HTML
        )
        return
    
    week_type = await index_weekday()
    
    await event.message.answer( 
        text=(
            f"Была выбрана группа : {groups.group_name}.\nТекущая неделя: {week_type}"
        ),
        attachments=[schedule_buttons()]
    )
    
    await context.update_data(
        group_name=groups.group_name,
        group_id=groups.id,
        entity_type="group"
    )
    
    await context.set_state(ScheduleState.waiting_group_day)

# today schedule
@dp.message_callback(F.callback.payload=="today")
async def print_schedule(event: MessageCallback, context: MemoryContext, session: AsyncSession):
    current_date = datetime.now()
    
    current_day= await check_weekend(datetime.today().weekday())
    current_week_type = await index_weekday(current_date.strftime("%Y-%m-%d"))
    
    current_state = await context.get_state()
    user_data = await context.get_data()

    match current_state:
        case ScheduleState.waiting_group_day:
            schedule = await get_group_schedule(
                session, current_day, user_data.get('group_id'), 
                user_data.get('group_name'), current_date.strftime("%Y-%m-%d")
            )
        case ScheduleState.waiting_teacher_day:
            schedule = await get_teacher_schedule(
                session, current_day, user_data.get('teacher_id'), current_date.strftime("%Y-%m-%d"),
                current_week_type
            )
        case _:
            schedule = "Ничего не найдено"
    
    await event.message.delete()
    await event.message.answer(
        text=(f"{schedule}"),
        attachments=[back_to_menu()],
        parse_mode=ParseMode.HTML
    )

# tomorrow schedule
@dp.message_callback(F.callback.payload=="tomorrow")
async def print_schedule(event: MessageCallback, context: MemoryContext, session: AsyncSession):
    tomorrow = datetime.now() + timedelta(days=1)
    
    current_day= await check_weekend(tomorrow.weekday())
    current_week_type = await index_weekday(tomorrow.strftime("%Y-%m-%d"))
    
    current_state = await context.get_state()
    user_data = await context.get_data()
    
    match current_state:
        case ScheduleState.waiting_group_day:
            schedule = await get_group_schedule(
                session, current_day, user_data.get('group_id'), 
                user_data.get('group_name'), tomorrow.strftime("%Y-%m-%d"), 
                current_week_type
            )
        case ScheduleState.waiting_teacher_day:
            schedule = await get_teacher_schedule(
                session, current_day, 
                user_data.get('teacher_id'), tomorrow.strftime("%Y-%m-%d"), 
                current_week_type
            )
        case _:
            schedule = "Ничего не найдено"
    
    await event.message.delete()
    await event.message.answer(
        text=(f"{schedule}"),
        attachments=[back_to_menu()],
        parse_mode=ParseMode.HTML
    )
    
# day after tomorrow's schedule
@dp.message_callback(F.callback.payload=="next_tomorrow")
async def print_schedule(event: MessageCallback, context: MemoryContext, session: AsyncSession):
    next_tomorrow = datetime.now() + timedelta(days=2)
    
    current_day= await check_weekend(next_tomorrow.weekday())
    current_week_type = await index_weekday(next_tomorrow.strftime("%Y-%m-%d"))
    
    current_state = await context.get_state()
    user_data = await context.get_data()
    
    match current_state:
        case ScheduleState.waiting_group_day:
            schedule = await get_group_schedule(
                session, current_day, user_data.get('group_id'), 
                user_data.get('group_name'), next_tomorrow.strftime("%Y-%m-%d"), 
                current_week_type
            )
        case ScheduleState.waiting_teacher_day:
            schedule = await get_teacher_schedule(
                session, current_day, 
                user_data.get('teacher_id'), next_tomorrow.strftime("%Y-%m-%d"), 
                current_week_type
            )
        case _:
            schedule = "Ничего не найдено"
            
    await event.message.delete()
    await event.message.answer(
        text=(f"{schedule}"),
        attachments=[back_to_menu()],
        parse_mode=ParseMode.HTML
    )


# in 2 days
@dp.message_callback(F.callback.payload=="in_2_days")
async def print_schedule(event: MessageCallback, context: MemoryContext, session: AsyncSession):
    two_days_after = datetime.now() + timedelta(days=3)
    
    current_day= await check_weekend(two_days_after.weekday())
    current_week_type = await index_weekday(two_days_after.strftime("%Y-%m-%d"))
    
    current_state = await context.get_state()
    user_data = await context.get_data()
    
    match current_state:
        case ScheduleState.waiting_group_day:
            schedule = await get_group_schedule(
                session, current_day, user_data.get('group_id'), 
                user_data.get('group_name'), two_days_after.strftime("%Y-%m-%d"), 
                current_week_type
            )
        case ScheduleState.waiting_teacher_day:
            schedule = await get_teacher_schedule(
                session, current_day, 
                user_data.get('teacher_id'), two_days_after.strftime("%Y-%m-%d"), 
                current_week_type
            )
        case _:
            schedule = "Ничего не найдено"
    
    await event.message.delete()
    await event.message.answer(
        text=(f"{schedule}"),
        attachments=[back_to_menu()],
        parse_mode=ParseMode.HTML
    )
    
# this week schedule
@dp.message_callback(F.callback.payload=="this_week")
async def print_schedule(event: MessageCallback, context: MemoryContext, session: AsyncSession):
    monday = get_current_week_monday()
    current_week_type = await index_weekday(monday.strftime("%Y-%m-%d"))
    current_day= await check_weekend(monday.weekday())
    
    current_state = await context.get_state()
    user_data = await context.get_data()
   
    match current_state:
        case ScheduleState.waiting_group_day:
            schedule = await get_group_schedule(
                session, current_day, user_data.get('group_id'), 
                user_data.get('group_name'), monday.strftime("%Y-%m-%d"), 
                current_week_type
            )
            
        case ScheduleState.waiting_teacher_day:
            schedule = await get_teacher_schedule(
                session, current_day, 
                user_data.get('teacher_id'), 
                monday.strftime("%Y-%m-%d"), current_week_type
            )
               
        case _:
            schedule = "Ничего не найдено"
   
    await event.message.delete()
    await event.message.answer(
        text=(f"{schedule}"),
        parse_mode=ParseMode.HTML,
        attachments=[week_schedule_buttons(current_day)]
    )
    
    await context.update_data(
                day=monday,
                type = 'this_week',
                entity_type="schedule_type"
            )
   
# next week's schedule
@dp.message_callback(F.callback.payload=="next_week")
async def print_schedule(event: MessageCallback, context: MemoryContext, session: AsyncSession):
    current_state = await context.get_state()
    user_data = await context.get_data()
    
    monday = get_next_week_monday()
    current_week_type = await index_weekday(monday.strftime("%Y-%m-%d"))
    current_day= await check_weekend(monday.weekday())
    
    match current_state:
        case ScheduleState.waiting_group_day:
            schedule = await get_group_schedule(
                session, current_day, user_data.get('group_id'), 
                user_data.get('group_name'), monday.strftime("%Y-%m-%d"), 
                current_week_type
            )
            
        case ScheduleState.waiting_teacher_day:
            schedule = await get_teacher_schedule(
                session, current_day, user_data.get('teacher_id'), 
                monday.strftime("%Y-%m-%d"), current_week_type
            )
               
        case _:
            schedule = "Ничего не найдено"
            
    await event.message.delete()
    await event.message.answer(
            text=(f"{schedule}"),
            parse_mode=ParseMode.HTML,
            attachments=[week_schedule_buttons(current_day)]
        )
    
    await context.update_data(
            day=monday,
            type = 'next_week',
            entity_type="schedule_type"
        )

# next day schedule
@dp.message_callback(F.callback.payload=="next_day")
async def print_schedule(event: MessageCallback, context: MemoryContext, session: AsyncSession):
    current_state = await context.get_state()
    user_data = await context.get_data()
    
    next_day = user_data.get('day') + timedelta(days=1)
    current_week_type = await index_weekday(next_day.strftime("%Y-%m-%d"))
    current_day= await check_weekend(next_day.weekday())
    await event.message.delete()
    
    match current_state:
        case ScheduleState.waiting_group_day:
            schedule = await get_group_schedule(
                session, current_day, user_data.get('group_id'), 
                user_data.get('group_name'), next_day.strftime("%Y-%m-%d"), 
                current_week_type
            )
            
        case ScheduleState.waiting_teacher_day:
            schedule = await get_teacher_schedule(
                session, current_day, user_data.get('teacher_id'), 
                next_day.strftime("%Y-%m-%d")
            )
               
        case _:
            schedule = "Ничего не найдено"
   
    await event.message.answer(
        text=(f"{schedule}"),
        parse_mode=ParseMode.HTML,
        attachments=[week_schedule_buttons(current_day)]
    )
   
    await context.update_data(
        day=next_day,
        type = user_data.get('type'),
        entity_type="schedule_type"
    )

# previous day schedule
@dp.message_callback(F.callback.payload=="previous_day")
async def print_schedule(event: MessageCallback, context: MemoryContext, session: AsyncSession):
    current_state = await context.get_state()
    user_data = await context.get_data()
    
    previous_day = user_data.get('day') - timedelta(days=1)
    current_week_type = await index_weekday(previous_day.strftime("%Y-%m-%d"))
    current_day= await check_weekend(previous_day.weekday())
    
    await event.message.delete()
        
    match current_state:
        case ScheduleState.waiting_group_day:
            schedule = await get_group_schedule(
                session, current_day, user_data.get('group_id'), 
                user_data.get('group_name'), previous_day.strftime("%Y-%m-%d"), 
                current_week_type
            )
            
        case ScheduleState.waiting_teacher_day:
            schedule = await get_teacher_schedule(
                session, current_day, user_data.get('teacher_id'), 
                previous_day.strftime("%Y-%m-%d")
            )
               
        case _:
            schedule = "Ничего не найдено"
            
    await event.message.answer(
        text=(f"{schedule}"),
        parse_mode=ParseMode.HTML,
        attachments=[week_schedule_buttons(current_day)]
    )
    
    await context.update_data(
        day=previous_day,
        type = user_data.get('type'),
        entity_type="schedule_type"
    )

# show menu 
@dp.message_callback(F.callback.payload=="back_menu")
async def return_menu(event: MessageCallback, context: MemoryContext):
    user_data = await context.get_data()
    
    current_teacher = user_data.get("teacher_name")
    current_group = user_data.get("group_name")
    
    if current_teacher is None: current_teacher = "Не выбрано"
    if current_group is None: current_group = "Не выбрано"
    
    await event.message.delete()
    await event.message.answer(
        text=(f"Главное меню\n<b>Преподаватель</b> - {current_teacher}\n<b>Группа</b> - {current_group}"),
        attachments=[schedule_buttons()],
        parse_mode=ParseMode.HTML
    )

# show main menu
@dp.message_callback(F.callback.payload=="main_menu")
async def return_menu(event: MessageCallback, context: MemoryContext):
    await event.message.delete()
    await event.message.answer(
        text=(
        "Добро пожаловать в бот расписания!\n\n"
        "Я помогу вам найти расписание:\n"
        "\t• Академических групп\n"  
        "\t• Преподавателей\n\n"
        "Используйте кнопки ниже для навигации"
    ),
        attachments=[start_keyboard()]
    )
    
# other invalid input
@dp.message_created(F.message.body.text)
async def handle_group_change(event: MessageCreated, context: MemoryContext, session: AsyncSession):
    user_input = event.message.body.text.strip().upper()
    #user_data = await context.get_data()
    
    patterns = [
        r'^[А-ЯЁA-Z]+-\d+[А-ЯЁA-Z]*$',
        r'^[А-ЯЁA-Z]+\d+[А-ЯЁA-Z]*$',
        r'^[а-яёa-z]?[А-ЯЁA-Z]+-\d+[А-ЯЁA-Z]*$',
        r'^[а-яёa-z]?[А-ЯЁA-Z]+\d+[А-ЯЁA-Z]*$',
        r'^[А-ЯЁA-Z]+\s[А-ЯЁA-Z]+-\d+[А-ЯЁA-Z]*$',
    ]
    
    if any(re.match(pattern, user_input) for pattern in patterns) and await context.get_state() == ScheduleState.waiting_group_day:
        exists, group = await check_group_exists(session, user_input)
        if exists == False:
            await event.message.answer(
                text=('Неизвестная группа. Для указания группы используйте команду <pre>/group</pre>'),
                parse_mode=ParseMode.HTML
            )
            return
           
        await context.update_data(
            group_name=group[1],
            group_id=group[0],
            entity_type="group"
        )
        
        await event.message.answer(
            text=(f'<b>Группа была изменена на {group.group_name}.</b>\nИспользуйте кнопки для просмотра расписания'),
            attachments=[schedule_buttons()],
            parse_mode=ParseMode.HTML
        )
        
        await context.set_state(ScheduleState.waiting_group_day)  
    
    elif await context.get_state() == ScheduleState.waiting_teacher_day:
        await event.message.answer(
            text=(f'Для смены преподователя воспользуйтесь командой <pre>/teacher</pre>'),
            parse_mode=ParseMode.HTML
        )
    
    else:
        await event.message.answer(
            text=(f'Неизвестный ввод. Воспользуйтесь командой <pre>/start</pre>'),
            parse_mode=ParseMode.HTML
        )