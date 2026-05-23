from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict, field_validator


class DepartmentCreate(BaseModel):
    """
    Модель для создания и обновления департамента.
    Используется в POST и PUT запросах.
    """
    name: str = Field(..., min_length=1, max_length=200,
                      description="Название департамента(3-50 символов)")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str):
        value = value.strip()

        if not value:
            raise ValueError("Name cannot be empty")

        return value

    parent_id: int | None = Field(None, description="ID родительского департамента, если есть")


class Department(BaseModel):
    """
    Модель для ответа с данными департамента.
    Используется в GET-запросах.
    """
    id: int = Field(..., description="Уникальный идентификатор департамента")
    name: str = Field(..., min_length=1, max_length=200, description="Название департамента")
    parent_id: int | None = Field(None, description="ID родительского департамента, если есть")
    created_at: datetime = Field(..., description="Дата создания департамента")
    is_active: bool = Field(..., description="Активность департамента")  # используется для мягкого удаления
    # employees: list['Employee'] | None = Field(list('Employee'), description="Сотрудники")
    # children: list['Department'] | None = Field(list('Department'), description="Дочерние департаменты")

    model_config = ConfigDict(from_attributes=True)


class EmployeeCreate(BaseModel):
    """
    Модель для создания и обновления сотрудника.
    Используется в POST и PUT запросах.
    """
    department_id: int = Field(..., description="Уникальный идентификатор департамента")
    full_name: str = Field(..., min_length=1, max_length=200, description="ФИО сотрудника")

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str):
        value = value.strip()

        if not value:
            raise ValueError("Full name cannot be empty")

        return value

    position: str = Field(..., min_length=3, max_length=50, description="Занимаемая должность")

    @field_validator("position")
    @classmethod
    def validate_position(cls, value: str):
        value = value.strip()

        if not value:
            raise ValueError("Position cannot be empty")

        return value

    hired_at: datetime | None = Field(None, description="Дата трудоустройства")


class Employee(BaseModel):
    """
    Модель для ответа с данными департамента.
    Используется в GET-запросах.
    """
    id: int = Field(..., description="Уникальный идентификатор сотрудника")
    department_id: int = Field(..., description="Уникальный идентификатор департамента")
    full_name: str = Field(..., min_length=1, max_length=200, description="ФИО сотрудника")
    position: str = Field(..., min_length=3, max_length=50, description="Занимаемая должность")
    hired_at: datetime = Field(..., description="Дата трудоустройства")
    created_at: datetime = Field(..., description="Дата регистрации сотрудника")
    is_active: bool = Field(..., description="Активность сотрудника")  # используется для мягкого удаления

    model_config = ConfigDict(from_attributes=True)


class DeleteDepartmentRequest(BaseModel):
    mode: str = Field(..., pattern="^(cascade|reassign)$", description="Принцип удаления")
    reassign_to_department_id: int | None = Field(None, description="Перенаправить сотрудников")
