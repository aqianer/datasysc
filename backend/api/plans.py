from datetime import datetime, timedelta
from typing import List, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models, schemas, auth
from config import settings
from database import get_db
import uuid
from logger import get_logger

logger = get_logger(__name__)

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


def get_plan_duration_from_toggl(db: Session, user_id: int, project_id: int, date: date) -> float:
    """从toggl_datas表获取特定日期特定项目的时长（分钟）"""
    # 获取最新的toggl数据
    toggl_data = db.query(models.TogglData).filter(
        models.TogglData.user_id == user_id
    ).order_by(
        models.TogglData.update_time.desc()
    ).first()
    
    if not toggl_data:
        return 0
    
    try:
        # 解析time_entries
        time_entries = toggl_data.time_entries
        
        # 计算指定日期和项目的总时长
        total_duration = 0
        date_str = date.strftime('%Y-%m-%d')
        
        for entry in time_entries:
            entry_date = datetime.fromisoformat(entry['start']).date()
            if (entry_date == date and 
                entry.get('pid') == project_id and 
                entry.get('duration', 0) > 0):
                # Toggl API返回的duration单位是秒，转换为分钟
                total_duration += entry['duration'] / 60
        
        return total_duration
    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"Error processing Toggl data: {str(e)}")
        return 0

@router.get("/heatmap", response_model=List[schemas.DailyStatus])
def get_heatmap_data(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
    plan_type: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """获取用户的热力图数据"""
    # 1. 设置日期范围
    today = datetime.now().date()
    if start_date and end_date:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
    else:
        end = today
        start = end - timedelta(days=365)  # 默认获取过去一年的数据

    # 2. 获取当前用户的有效计划
    plans_query = db.query(models.PersonalPlan).filter(
        models.PersonalPlan.user_id == current_user.id,
        models.PersonalPlan.plan_status == 2  # 进行中的计划
    )
    
    if plan_type is not None:
        plans_query = plans_query.filter(models.PersonalPlan.plan_type == plan_type)
    
    active_plans = plans_query.all()

    # 3. 获取现有的daily_status记录
    existing_status = {
        status.record_date: status
        for status in db.query(models.DailyStatus).filter(
            models.DailyStatus.user_id == current_user.id,
            models.DailyStatus.record_date.between(start, end)
        ).all()
    }

    # 4. 生成或更新每日状态数据
    result_data = []
    current_date = start
    while current_date <= end:
        # 如果是今天之后的日期，跳过
        if current_date > today:
            current_date += timedelta(days=1)
            continue

        # 获取或创建当日状态
        daily_status = existing_status.get(current_date)
        
        if not daily_status:
            # 为当前日期创建新的状态记录
            plan_status = {}
            total_duration = 0
            completed_core_plans = 0
            total_core_plans = 0

            for plan in active_plans:
                # 检查计划在当前日期是否有效
                if plan.create_time.date() <= current_date <= plan.deadline:
                    # 从toggl_datas获取实际时长
                    actual_duration = get_plan_duration_from_toggl(
                        db, 
                        current_user.id,
                        plan.toggl_project_id,
                        current_date
                    )
                    
                    is_completed = actual_duration >= plan.daily_plan_duration
                    
                    plan_status[plan.plan_name] = {
                        "completed": is_completed,
                        "plan_type": plan.plan_type,
                        "duration": actual_duration
                    }
                    
                    total_duration += actual_duration
                    if plan.plan_type == 1:  # 核心计划（每日必做）
                        total_core_plans += 1
                        if is_completed:
                            completed_core_plans += 1

            # 计算热力等级
            if total_core_plans == 0:
                heat_level = 0
            else:
                completion_rate = completed_core_plans / total_core_plans
                if completion_rate == 1:
                    heat_level = 4
                elif completion_rate >= 0.75:
                    heat_level = 3
                elif completion_rate >= 0.5:
                    heat_level = 2
                elif completion_rate > 0:
                    heat_level = 1
                else:
                    heat_level = 0

            # 创建新的daily_status记录
            daily_status = models.DailyStatus(
                user_id=current_user.id,
                record_date=current_date,
                plan_status=plan_status,
                heat_level=heat_level,
                total_duration=total_duration,
                is_core_completed=(completed_core_plans == total_core_plans)
            )
            db.add(daily_status)

        # 添加到结果列表
        result_data.append({
            "record_date": daily_status.record_date,
            "plan_status": daily_status.plan_status,
            "heat_level": daily_status.heat_level
        })
        
        current_date += timedelta(days=1)

    # 提交数据库更改
    db.commit()
    
    return result_data
