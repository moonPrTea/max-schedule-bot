from sqlmodel import Field, SQLModel


class StudentSchedule(SQLModel, table=True):
    __tablename__ = "student_schedule"
    id: int = Field(default=None, primary_key=True)
    numerator_denominator: int
    lesson_date: str
    weekday: str
    subject: str
    id_teacher: int = Field(foreign_key="employee.id", nullable=True)
    number_classroom: str = Field(default=None, nullable=True)
    number_subgroup: int = Field(default=None, nullable=True)
    lesson_type: str
    time_lesson_starts: str  # TIME
    time_lesson_ends: str  # TIME
    id_group: int = Field(foreign_key="st_group.id")
    education_form: str = Field(default=None, nullable=True)
