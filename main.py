# WorkBoard API project
# WB-001: Creating and viewing tasks
# WB-002 - Update and Delete Tasks
# WB-003 - Task Filtering
# WB-004 - Task Sorting and Pagination
# WB-005 - Dependency Injection
# WB-006 - Authentication with OAuth2 and JWT
# WB-007 - User Registration
# WB-008 - Database Persistence with SQLAlchemy
# WB-009 - # WB-008 - Database Persistence with SQLAlchemy
# WB-010 - user task isolation
# WB-011 - settings and API routers
# Wb-12  - tests
from fastapi import FastAPI, status

from routers import users, tasks

app = FastAPI()
app.include_router(users.router)
app.include_router(tasks.router)


@app.get("/health", status_code=status.HTTP_200_OK)
async def get_health():
    return {"status": "ok"}
