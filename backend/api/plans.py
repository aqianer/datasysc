from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict
import models, schemas, auth
from config import settings
from database import get_db
import uuid

router = APIRouter()


@router.post("/", response_model=schemas.PlanResponse)
def create_plan(
        plan: schemas.PlanCreate,
        current_user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(get_db)
):
    # 生成一个随机的 plan_id
    plan_id = str(uuid.uuid4())  # 生成一个随机的 UUID
    db_plan = models.PersonalPlan(
        plan_id=plan_id,  # 将生成的 plan_id 存入数据库
        **plan.dict(),
        user_id=current_user.id,
        plan_status=2,  # 默认为进行中
        create_time=datetime.now(),  # 手动提供 create_time
        update_time=datetime.now()  # 手动提供 update_time

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


@router.get("/heatmap", response_model=List[schemas.DailyStatus])
def get_heatmap_data(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的热力图数据"""
    # TODO: 这里先返回模拟数据，后续需要从daily_status表获取实际数据
    today = datetime.now().date()
    start_date = today - timedelta(days=365)  # 获取过去一年的数据
    
    # 生成模拟数据
    mock_data = []
    current_date = start_date
    while current_date <= today:
        # 生成随机的计划完成详情
        plan_status = {
            "计划A": {
                "completed": True,
                "plan_type": 1,
                "duration": 45
            },
            "计划B": {
                "completed": False,
                "plan_type": 2,
                "duration": 28
            }
        }
        
        # 根据日期生成不同的热力等级
        weekday = current_date.weekday()
        if weekday < 5:  # 工作日
            heat_level = min(4, max(1, (weekday + 1) % 5))
        else:  # 周末
            heat_level = max(0, weekday % 2)
        
        mock_data.append({
            "record_date": current_date,
            "plan_status": plan_status,
            "heat_level": heat_level
        })
        
        current_date += timedelta(days=1)
    
    return mock_data
