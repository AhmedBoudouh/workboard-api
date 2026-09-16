#WorkBoard API project
# Requirement WB-001: Creating and viewing tasks

from fastapi import FastAPI, HTTPException ,status
from pydantic import BaseModel, Field
from enum import Enum 
import itertools
from datetime import UTC, datetime, timezone
from typing import Annotated

app=FastAPI()
tasks_db=[]

_id_counter= itertools.count(1)
def next_id()-> int:
    return next(_id_counter)

class StatusVar(str,Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"
    
class PriorityVar(str,Enum):
    low = "low"
    medium = "medium"
    high = "high"
    
    
    

class TasksIn(BaseModel):
    title: str = Field(min_length =3, max_length=100)
    description: str| None = Field(default=None, max_length=500 )
    priority: PriorityVar =Field(default=PriorityVar.medium)
    

class TasksOut(TasksIn):    
    id: int
    status: StatusVar =Field(default=StatusVar.todo)
    created_at: datetime
    
class UpdateData(BaseModel):
        
        title: str  = Field(default=None, min_length =3, max_length=100)
        description: str| None = Field(default=None, max_length=500 )
        priority: PriorityVar | None =None
        status: StatusVar |None =None  
        
def extract_task (item) -> TasksOut| None:
    for task in tasks_db:
            if task.id == item:
              return task       
        


 
    
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
      task =extract_task (task_id)
      if not task:
          raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="task mot found")
      return task
      
    
    
    
    ##WB-002 — Update and Delete Tasks
@app.patch("/tasks/{task_id}", status_code=status.HTTP_200_OK) 
async def update_tasks(task_id:int,data:UpdateData ):
    task = extract_task (task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="task mot found")
   
    stored_data= task.model_dump()
    updated_data = data.model_dump(exclude_unset=True)
    
    for key in updated_data:
        # if key =="title" and updated_data['title'] is None:     don't need it the class UpdateData did it (pydantic validation)
        #     raise HTTPException(status_code=404,detail="titles couldn't be null")
            
        if updated_data[key] != stored_data[key]:
             setattr(task,key,updated_data[key])
    return task
        
  
    # if data.title :
    #   task.title = data.title
    # if data.description==  "":
    #         task.description= ""
    # if data.description:
    #     task.description= data.description
        
    # if data.priority:       
    #     task.priority = data.priority
    # if data.status:    
    #     task.status =data.status
    
    # return task

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id:int):
    task = extract_task(task_id) 
    if not task:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No content")
    tasks_db.remove(task)
   
    

    


