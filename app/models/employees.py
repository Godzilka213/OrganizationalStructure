from datetime import datetime, date
from app.database import Base
from sqlalchemy import ForeignKey, func, String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id", ondelete="CASCADE"), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    position: Mapped[str] = mapped_column(String(100), nullable=False)
    hired_at: Mapped[date | None] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    department: Mapped["Department"] = relationship(
        "Department",  # Имя связанной модели
        back_populates="employees"  # Имя атрибута обратной связи в Department
    )
