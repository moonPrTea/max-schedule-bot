from sqlmodel import SQLModel, Field


class Employee(SQLModel, table=True):
    __tablename__ = "employee"
    id: int = Field(default=None, primary_key=True)
    surname: str
    name: str
    patronymic: str
