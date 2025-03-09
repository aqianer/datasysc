from decimal import Decimal

import pytz
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
import models, schemas, auth
from database import get_db

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_stats(
        current_user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(get_db)
):
    # 获取当前时间和本周开始时间
    now = datetime.now()
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

    # 获取本周Toggl统计数据
    toggl_data = db.query(models.TogglData).filter(
        models.TogglData.user_id == current_user.id
    ).order_by(desc(models.TogglData.update_time)).first()

    total_duration = 0
    project_toggl_detail = []
    if toggl_data and toggl_data.time_entries:
        for entry in toggl_data.time_entries:
            entry_start = datetime.strptime(entry['start'], '%Y-%m-%dT%H:%M:%S%z')
            week_start_aware = pytz.UTC.localize(week_start)

            # 确保 week_start 是 datetime 对象
            if entry_start >= week_start_aware and entry['duration'] > 0:
                total_duration += entry['duration'] / 3600  # 转换为小时
                project_toggl_detail.append({
                    'project_id': entry['project_id'],
                    'duration': entry['duration'] / 3600,
                    'at': entry_start,
                })
    # 获取本周GitHub统计数据
    github_events = db.query(models.GitHubEvents).filter(
        models.GitHubEvents.user_id == current_user.id,
        models.GitHubEvents.event_time >= week_start
    ).all()

    event_counts = {
        'total_events': len(github_events),
        'commits': sum(1 for e in github_events if e.event_type == 'PushEvent'),
        'pulls': sum(1 for e in github_events if e.event_type == 'PullRequestEvent'),
        'issues': sum(1 for e in github_events if e.event_type == 'IssuesEvent'),
        'daily_events': []
    }

    # 统计每日事件数
    daily_counts = {}
    for event in github_events:
        date_str = event.event_time.date().isoformat()
        daily_counts[date_str] = daily_counts.get(date_str, 0) + 1

    event_counts['daily_events'] = [
        {'date': date, 'count': count}
        for date, count in sorted(daily_counts.items())
    ]

    # 获取计划统计数据
    plans = db.query(models.PersonalPlan).filter(
        models.PersonalPlan.user_id == current_user.id,
    ).all()

    plan_stats = {
        'total': len(plans),
        'completed': sum(1 for p in plans if p.plan_status == 1),
        'inProgress': sum(1 for p in plans if p.plan_status == 2),
        'delayed': sum(1 for p in plans if p.plan_status == 0),
        'distribution': []
    }
    target_hour = 0
    for plan in plans:
        plan_time = sum(
            toggl_detail['duration'] for toggl_detail in project_toggl_detail
            if toggl_detail.get('project_id') is not None and toggl_detail['project_id'] == plan.toggl_project_id
        )
        percentage = 0 if total_duration <= 0 else plan_time / total_duration * 100
        target_hour += plan.daily_plan_duration
        plan_stats['distribution'].append({
            'plan_name': plan.plan_name,
            'duration': round(plan_time, 2),
            'percentage': round(percentage, 2),
            'plan_type': plan.plan_type,
            'color': get_plan_color(len(plan_stats['distribution']))
        })
    week_target = target_hour * 5

    return {
        'stats': {
            'toggl': {
                'actual_hours': round(total_duration, 1),
                'target_hours': week_target,  # 可以从配置或用户设置中获取
                'completion_rate': round((total_duration / float(week_target)) * 100, 2),
                'period': '本周'
            },
            'github': event_counts,
            'plans': plan_stats
        }
    }


def get_plan_color(index: int) -> str:
    """根据索引返回计划颜色"""
    colors = [
        '#409EFF',  # 蓝色
        '#67C23A',  # 绿色
        '#E6A23C',  # 橙色
        '#F56C6C',  # 红色
        '#909399',  # 灰色
        '#9B59B6',  # 紫色
        '#3498DB',  # 浅蓝
        '#1ABC9C',  # 青绿
        '#F1C40F',  # 黄色
        '#E74C3C'  # 深红
    ]
    return colors[index % len(colors)]
