from datetime import datetime, timedelta, date


async def check_weekend(day): 
    day = str(day)
    weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
    return weekdays[int(day)]


async def index_weekday(dates: str | None = None) -> str:
    if dates:
        if isinstance(dates, str):
            dates = datetime.strptime(dates, "%Y-%m-%d")
        elif isinstance(dates, datetime):
            pass
        elif isinstance(dates, date):
            dates = datetime.combine(dates, datetime.min.time())
        
        today = dates.date()
        current_year = dates.year
        current_month = dates.month
        now = dates
    else:
        now = datetime.now()
        current_year = now.year
        current_month = now.month
        today = date.today()
    
    week_number = today.isocalendar()[1] + 1

    if current_month >= 9:
        first_week_september = datetime(current_year, 9, 1).isocalendar()[1]
        if first_week_september % 2 == 0:
            s = 1
        else:
            s = 0
    else:
        previous_year = current_year - 1
        first_week_september = datetime(previous_year, 9, 1).isocalendar()[1]
        print(first_week_september)
        if first_week_september % 2 == 0:
            s = 1
        else:
            s = 0

    if week_number % 2 == s:
        return 'Числитель'
    
    return 'Знаменатель'


# get monday date of current week
def get_current_week_monday(current_date: datetime = None) -> datetime:
    if current_date is None:
        current_date = datetime.now()
    days_since_monday = current_date.weekday()
    return current_date - timedelta(days=days_since_monday)

# get monday date of next week
def get_next_week_monday(current_date: datetime = None) -> datetime:
    current_monday = get_current_week_monday(current_date)
    return current_monday + timedelta(days=7)

# get lesson number in schedule
async def get_number_lesson(lesson_time):
    schedule_time = {
        "08:30:00": '1', "08:00:00": '1',
        "10:15:00": '2', "09:45:00": '2',
        "12:00:00": '3', "11:30:00": '3',
        "14:20:00": '4', "13:30:00": '4',
        "16:05:00": '5', "15:15:00": '5',
        "17:50:00": '6', "17:00:00": '6',
        "18:40:00": '7', "19:35:00": '7'
    }
    return schedule_time.get(lesson_time)