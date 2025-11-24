from sqlmodel import SQLModel, Field


class StudentGroup(SQLModel, table=True):
    __tablename__ = "st_group"
    id: int = Field(default=None, primary_key=True)
    group_name: str
    id_1c: str
