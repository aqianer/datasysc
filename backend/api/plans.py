from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import models, schemas, auth
from config import settings
from database import get_db

router = APIRouter()

@router.post("/", response_model=schemas.PlanResponse)
def create_plan(
    plan: schemas.PlanCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    db_plan = models.PersonalPlan(
        **plan.dict(),
        user_id=current_user.id,
        plan_status=2  # 默认为进行中
    )
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan

@router.get("/", response_model=List[schemas.PlanResponse])
def get_plans(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(models.PersonalPlan).filter(
        models.PersonalPlan.user_id == current_user.id
    ).all()

@router.put("/{plan_id}", response_model=schemas.PlanResponse)
def update_plan(
    plan_id: int,
    plan_update: schemas.PlanUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    db_plan = db.query(models.PersonalPlan).filter(
        models.PersonalPlan.id == plan_id,
        models.PersonalPlan.user_id == current_user.id
    ).first()
    
    if not db_plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    for key, value in plan_update.dict(exclude_unset=True).items():
        setattr(db_plan, key, value)
    
    db.commit()
    db.refresh(db_plan)
    return db_plan

@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(
    plan_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    db_plan = db.query(models.PersonalPlan).filter(
        models.PersonalPlan.id == plan_id,
        models.PersonalPlan.user_id == current_user.id
    ).first()
    
    if not db_plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    db.delete(db_plan)
    db.commit() 