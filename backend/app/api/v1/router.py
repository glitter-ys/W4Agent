from fastapi import APIRouter

from app.api.v1.projects import router as projects_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.reports import router as reports_router
from app.api.v1.annotations import router as annotations_router
from app.api.v1.issues import router as issues_router
from app.api.v1.pages import router as pages_router

api_v1_router = APIRouter()

api_v1_router.include_router(projects_router)
api_v1_router.include_router(tasks_router)
api_v1_router.include_router(reports_router)
api_v1_router.include_router(annotations_router)
api_v1_router.include_router(issues_router)
api_v1_router.include_router(pages_router)
