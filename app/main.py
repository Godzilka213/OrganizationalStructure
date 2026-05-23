from fastapi import FastAPI
from app.routers import departaments

app = FastAPI(
    title="FastAPI Organizational Structure",
    version="0.1.0",
)

# Подключаем маршруты департамента
app.include_router(departaments.router)


# Корневой эндпоинт для проверки
@app.get("/")
async def root():
    """
    Корневой маршрут, подтверждающий, что API работает.
    """
    return {"message": "Добро пожаловать в API организационную структуру!"}
