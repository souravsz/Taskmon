from fastapi import APIRouter

from app.api.v1 import auth, expenses, notes, reminders, users

api_v1_router = APIRouter()
api_v1_router.include_router(auth.router)
api_v1_router.include_router(users.router)
api_v1_router.include_router(reminders.router)
api_v1_router.include_router(expenses.router)
api_v1_router.include_router(notes.router)
