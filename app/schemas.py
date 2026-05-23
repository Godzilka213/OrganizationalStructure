from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict


class DepartmentCreate(BaseModel):
    """
    Модель для создания и обновления департамента.
    Используется в POST и PUT запросах.
    """
    name: str = Field(..., min_length=1, max_length=200,
                      description="Название департамента(3-50 символов)")
    parent_id: int | None = Field(None, description="ID родительского департамента, если есть")


class Department(BaseModel):
    """
    Модель для ответа с данными департамента.
    Используется в GET-запросах.
    """
    id: int = Field(..., description="Уникальный идентификатор департамента")
    name: str = Field(..., min_length=1, max_length=200, description="Название департамента")
    parent_id: int | None = Field(None, description="ID родительского департамента, если есть")
    is_active: bool = Field(..., description="Активность департамента")  # используется для мягкого удаления

    model_config = ConfigDict(from_attributes=True)


class EmployeeCreate(BaseModel):
    """
    Модель для создания и обновления сотрудника.
    Используется в POST и PUT запросах.
    """
    department_id: int = Field(..., description="Уникальный идентификатор департамента")
    full_name: str = Field(..., min_length=1, max_length=200, description="ФИО сотрудника")
    position: str = Field(..., min_length=3, max_length=50, description="Занимаемая должность")


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
