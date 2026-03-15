from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user_goal import UserGoal
from app.schemas.goals import UserGoalCreate, UserGoalResponse

router = APIRouter(prefix="/api/goals", tags=["goals"])


@router.get("", response_model=list[UserGoalResponse])
def get_goals(db: Session = Depends(get_db)):
    goals = db.query(UserGoal).all()
    return goals


@router.put("", response_model=list[UserGoalResponse])
def update_goals(goals_data: list[UserGoalCreate], db: Session = Depends(get_db)):
    results = []
    for goal_data in goals_data:
        existing = (
            db.query(UserGoal)
            .filter(UserGoal.metric_key == goal_data.metric_key)
            .first()
        )
        if existing:
            existing.target_value = goal_data.target_value
            existing.target_unit = goal_data.target_unit
            existing.category = goal_data.category
            results.append(existing)
        else:
            new_goal = UserGoal(
                metric_key=goal_data.metric_key,
                target_value=goal_data.target_value,
                target_unit=goal_data.target_unit,
                category=goal_data.category,
            )
            db.add(new_goal)
            results.append(new_goal)
    db.commit()
    for r in results:
        db.refresh(r)
    return results
