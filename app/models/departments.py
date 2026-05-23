from datetime import datetime
from app.database import Base
from sqlalchemy import ForeignKey, func, String, DateTime, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Department(Base):
    __tablename__ = "departments"
    __table_args__ = (
        UniqueConstraint("name", "parent_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id", ondelete="CASCADE"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(),
                                                 nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Связь один-ко-многим, возвращает список объектов Employee
    employees: Mapped[list["Employee"]] = relationship(
        "Employee",  # Имя связанной модели
        back_populates="department",  # Имя атрибута обратной связи в Employee
        cascade="all, delete-orphan",  # Удаляет работников при удалении департамента
    )
    # Связь родительского департамента
    parent: Mapped["Department | None"] = relationship(
        "Department",
        back_populates="children",
        remote_side="Department.id"
    )
    # Связь, представляет список дочерних департаментов
    children: Mapped[list["Department"]] = relationship(
        "Department",
        back_populates="parent",
        cascade="all, delete-orphan",
    )
