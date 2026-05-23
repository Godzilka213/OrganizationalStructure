from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.db_depends import get_async_db
from app.models import Department as DepartmentModel, Employee as EmployeeModel
from app.schemas import Department as DepartmentSchema, Employee as EmployeeSchema, DepartmentCreate, EmployeeCreate

# Создаем маршрутизатор с префиксом и тегом
router = APIRouter(
    prefix="/departments",
    tags=["departments"]
)


@router.get("/")
async def get_departments(db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список всех активных департаментов
    """

    stmt = (
        select(DepartmentModel)
        .where(DepartmentModel.is_active == True)
        .options(selectinload(DepartmentModel.employees).
                 load_only(EmployeeModel.id, EmployeeModel.full_name, EmployeeModel.position))
    )
    departments = await db.scalars(stmt)
    return departments.all()


@router.post("/", response_model=DepartmentSchema, status_code=status.HTTP_201_CREATED)
async def create_department(
        department: DepartmentCreate = Depends(DepartmentCreate),
        db: AsyncSession = Depends(get_async_db)
):
    """Создает новый департамент"""
    # Проверка существования parent_id, если указан
    if department.parent_id is not None:
        parent = await db.scalar(select(DepartmentModel).where(DepartmentModel.id == department.parent_id,
                                                               DepartmentModel.is_active == True))
        if parent is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parent department not found")

    # Создание нового департамента
    db_department = DepartmentModel(**department.model_dump())
    db.add(db_department)
    await db.commit()
    return db_department


@router.post("/{department_id}/employees", response_model=EmployeeSchema,
             status_code=status.HTTP_201_CREATED)
async def create_employee(
        department_id: int,
        employee: EmployeeCreate = Depends(EmployeeCreate),
        db: AsyncSession = Depends(get_async_db),
):
    """
    Создает нового сотрудника в определенном департаменте
    """
    # Проверка существования департамента
    department = await db.scalar(
        select(DepartmentModel).where(
            DepartmentModel.id == department_id,
            DepartmentModel.is_active == True
        )
    )
    if department is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department not found")
    db_employee = EmployeeModel(**employee.model_dump())
    db.add(db_employee)
    await db.commit()
    return db_employee


@router.patch('/{department_id}', response_model=DepartmentSchema)
async def update_department(
        department_id: int,
        name: str | None = None,
        parent_id: int | None = None,
        db: AsyncSession = Depends(get_async_db),
):
    """
    Перемещает подразделение в другое изменяя parent_id
    """
    check_department_id = await db.scalar(select(DepartmentModel).where(
        DepartmentModel.id == department_id,
        DepartmentModel.is_active == True)
    )
    # Проверяем активность department_id
    if check_department_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department not found")
    # Проверяем активность parent_id
    if parent_id is not None:
        check_parent_id = await db.scalar(select(DepartmentModel).where(
            DepartmentModel.id == parent_id,
            DepartmentModel.is_active == True)
        )
        if check_parent_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parent department not found")

    await db.execute(
        update(DepartmentModel)
        .where(DepartmentModel.id == department_id)
        .values(name=name if name is not None else DepartmentModel.name,
                parent_id=parent_id if parent_id is not None else DepartmentModel.parent_id)
    )
    await db.commit()
    return check_department_id


@router.delete('/{department_id}', response_model=DepartmentSchema)
async def delete_department(department_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Выполняет мягкое удаление департамента по его ID, устанавливая is_active = False
    """
    # Проверяем активность департамента
    department = await db.scalar(
        select(DepartmentModel).where(
            DepartmentModel.id == department_id,
            DepartmentModel.is_active == True)
    )
    if not department:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department not found")
    await db.execute(
        update(DepartmentModel)
        .where(DepartmentModel.id == department_id)
        .values(is_active=False)
    )
    await db.commit()
    return department
