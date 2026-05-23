from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.db_depends import get_async_db
from app.models import Department as DepartmentModel, Employee as EmployeeModel
from app.schemas import Department as DepartmentSchema, Employee as EmployeeSchema, DepartmentCreate, EmployeeCreate, \
    DeleteDepartmentRequest

# Создаем маршрутизатор с префиксом и тегом
router = APIRouter(
    prefix="/departments",
    tags=["departments"]
)


async def delete_department_reassign(
        db: AsyncSession,
        department_id: int,
        reassign_to_department_id: int
):
    """Удаляет департамент, переводя сотрудников и дочерние департаменты в другой департамент."""
    # Проверяем, что целевой департамент существует
    target_dept = await db.scalar(
        select(DepartmentModel)
        .where(DepartmentModel.id == reassign_to_department_id, DepartmentModel.is_active == True)
    )
    if not target_dept:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target department not found or inactive"
        )

    # Переводим сотрудников в новый департамент
    await db.execute(
        update(EmployeeModel)
        .where(EmployeeModel.department_id == department_id)
        .values(department_id=reassign_to_department_id)
    )

    # Находим все дочерние департаменты
    children = await db.scalars(
        select(DepartmentModel)
        .where(DepartmentModel.parent_id == department_id)
    )
    children_list = children.all()

    # Перепривязываем дочерние департаменты к целевому
    for child in children_list:
        child.parent_id = reassign_to_department_id

    # Удаляем сам департамент (теперь без дочерних ссылок)
    department = await db.get(DepartmentModel, department_id)
    if department:
        await db.delete(department)


@router.get("/")
async def get_departments(db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список всех активных департаментов
    """
    stmt = (
        select(DepartmentModel)
        .where(DepartmentModel.is_active == True)
        .options(selectinload(DepartmentModel.employees).
                 load_only(EmployeeModel.id,
                           EmployeeModel.full_name,
                           EmployeeModel.position,
                           EmployeeModel.department_id,
                           EmployeeModel.hired_at)
                 )
    )
    departments = await db.scalars(stmt)
    return departments.all()


@router.post("/", response_model=DepartmentSchema, status_code=status.HTTP_201_CREATED)
async def create_department(
        department: DepartmentCreate = Depends(DepartmentCreate),
        db: AsyncSession = Depends(get_async_db)
) -> DepartmentModel:
    """Создает новый департамент"""
    # Проверка существования parent_id, если указан
    if department.parent_id is not None:
        parent = await db.scalar(select(DepartmentModel).where(DepartmentModel.id == department.parent_id,
                                                               DepartmentModel.is_active == True))
        if parent is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Родительский департамент не найден")

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
) -> EmployeeModel:
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Департамент не найден")
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
) -> DepartmentModel:
    """
    Изменяет родительское подразделение parent_id
    """
    # Проверяем что текущий и новый ID департамента должны быть различны
    if department_id == parent_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Департамент не может быть родителем у самого себя"
        )
    check_department_id = await db.scalar(select(DepartmentModel).where(
        DepartmentModel.id == department_id,
        DepartmentModel.is_active == True)
    )
    # Проверяем активность department_id
    if check_department_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Департамент не найден")
    # Проверяем активность parent_id
    if parent_id is not None:
        check_parent_id = await db.scalar(select(DepartmentModel).where(
            DepartmentModel.id == parent_id,
            DepartmentModel.is_active == True)
        )
        if check_parent_id is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Родительский департамент не найден")

    await db.execute(
        update(DepartmentModel)
        .where(DepartmentModel.id == department_id)
        .values(name=name if name is not None else DepartmentModel.name,
                parent_id=parent_id if parent_id is not None else DepartmentModel.parent_id)
    )
    await db.commit()
    return check_department_id


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
        department_id: int,
        request: DeleteDepartmentRequest = Depends(DeleteDepartmentRequest),
        db: AsyncSession = Depends(get_async_db)
):
    """
    Удалить подразделение с выбором режима:
    - cascade: удалить подразделение, всех сотрудников и дочерние подразделения
    - reassign: удалить подразделение, сотрудников перевести в другой департамент
    """
    # Проверяем существование удаляемого департамента
    department = await db.scalar(
        select(DepartmentModel)
        .where(DepartmentModel.id == department_id, DepartmentModel.is_active == True)
    )
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )

    # Выполняем удаление в зависимости от режима
    if request.mode == "cascade":
        await db.delete(department)
    elif request.mode == "reassign":
        if request.reassign_to_department_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="reassign_to_department_id является обязательным"
            )
        await delete_department_reassign(db, department_id, request.reassign_to_department_id)

    await db.commit()
    return  # 204 No Content
