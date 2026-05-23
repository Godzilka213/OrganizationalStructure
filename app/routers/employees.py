from fastapi import APIRouter, Depends, HTTPException, status

# Создаем маршрутизатор с префиксом и тегом
router = APIRouter(
    prefix="employees",
    tags=["employees"]
)
