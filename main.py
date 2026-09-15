#WorkBoard API project
# Requirement WB-001: Creating and viewing tasks

from fastapi import FastAPI, HTTPException ,status
from pydantic import BaseModel, Field
from enum import Enum 
import itertools
from datetime import UTC, datetime, timezone

app=FastAPI()
tasks_db=[]

_id_counter= itertools.count(1)
def next_id()-> int:
    return next(_id_counter)
class Status_var(str,Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"
    
class Priority_var(str,Enum):
    low = "low"
    medium = "medium"
    high = "high"
    
    
    

class TasksIn(BaseModel):
    title: str = Field(min_length =3, max_length=100)
    description: str| None = Field(default=None, max_length=500 )
    priority: Priority_var =Field(default=Priority_var.medium)
    

class TasksOut(TasksIn):    
    id: int
    status: Status_var =Field(default=Status_var.todo)
    created_at: datetime
    
 
    
@app.get("/health", status_code=status.HTTP_200_OK)   
async def get_health():
     return {"status": "ok"}


@app.post("/tasks", status_code=201)   
async def create_tasks(taskin: TasksIn) -> TasksOut:
    task =TasksOut(**taskin.model_dump(),
    id =next_id(),
    created_at= datetime.now(timezone.utc),
    status="todo")
    tasks_db.append(task)
    return task

@app.get("/tasks")
async def get_tasks()->list[TasksOut]:
  return tasks_db

@app.get("/tasks/{task_id}",status_code=status.HTTP_200_OK)
async def get_tasks_by_id(task_id:int):
    for t in tasks_db:
        if t.id == task_id:
          return t
      
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="task mot found")
    