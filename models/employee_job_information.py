from sqlmodel import SQLModel, Field

class EmployeeJobInformation(SQLModel, table=True):
    __tablename__ = "employee_job_information"
    id: int = Field(default=None, primary_key=True)
    id_employee: int = Field(foreign_key="employee.id")
    id_bet: int = Field(foreign_key="bet.id")
    id_position: int = Field(foreign_key="employee_position.id")
    employment_type: str
    employee: bool