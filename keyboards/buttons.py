from maxapi.types import ButtonsPayload, CallbackButton
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder

# initial buttons
def start_keyboard() -> ButtonsPayload:
    buttons = [
        [CallbackButton(text='Расписание преподавателя', payload="teacher_schedule")],
        [CallbackButton(text='Расписание группы', payload="group_schedule")]
    ]
    
    return ButtonsPayload(buttons=buttons).pack()

# schedule buttons
def schedule_buttons() -> ButtonsPayload:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        CallbackButton(text='Сегодня', payload="today"),
        CallbackButton(text='Завтра', payload="tomorrow")
    )
    
    builder.row(
        CallbackButton(text='Послезавтра', payload="next_tomorrow"),
        CallbackButton(text='Через 2 дня', payload="in_2_days")
    )
    
    builder.row(
        CallbackButton(text="На неделю", payload="this_week"),
        CallbackButton(text="На следующую неделю", payload="next_week")
    )
    builder.row(
        CallbackButton(text="Общее меню", payload="main_menu")
    )
    
    return builder.as_markup()

# week schedule buttons
def week_schedule_buttons(day: str) -> ButtonsPayload:
    builder = InlineKeyboardBuilder()
    
    match day:
        case 'Понедельник':
            builder.row(
            CallbackButton(text="Понедельник", payload="__"),
            CallbackButton(text=">>", payload="next_day"),
            )
            
        case 'Суббота': 
            builder.row(
            CallbackButton(text="<<", payload="previous_day"),
            CallbackButton(text='Суббота', payload="__"),
            )
        case _:
            builder.row(
                CallbackButton(text="<<", payload="previous_day"),
                CallbackButton(text=f'{day}', payload="__"),
                CallbackButton(text=">>", payload="next_day"),
            )
    
    builder.row(
        CallbackButton(text="Меню", payload="back_menu")
    )
    
    return builder.as_markup() 

# back to menu button
def back_to_menu() -> ButtonsPayload:
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="Меню", payload="back_menu")
    )
    
    return builder.as_markup()
