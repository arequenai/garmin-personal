from pydantic import BaseModel


class SettingsResponse(BaseModel):
    hr_max: int
    hr_rest: int
    hr_threshold: int
    mfp_configured: bool = False

    model_config = {"from_attributes": True}


class SettingsUpdate(BaseModel):
    hr_max: int | None = None
    hr_rest: int | None = None
    hr_threshold: int | None = None
    mfp_cookies: str | None = None
