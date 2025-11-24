from maxapi.context import State, StatesGroup

"""
State - FSM state;
StatesGroup - group of states.
Based on the maxapi code, it works using MemoryContext.
"""

class ScheduleState(StatesGroup):
    group_name = State()
    waiting_group_day = State()
    teacher_name = State() 
    waiting_teacher_day = State() 