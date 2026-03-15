from pydantic import BaseModel


class UserGoalResponse(BaseModel):
    metric_key: str
    target_value: float
    target_unit: str
    category: str

    model_config = {"from_attributes": True}


class UserGoalCreate(BaseModel):
    metric_key: str
    target_value: float
    target_unit: str
    category: str
