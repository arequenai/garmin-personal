from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://garmin:garmin_dev@localhost:5435/garmin_personal"
    garmin_email: str = ""
    garmin_password: str = ""
    mfp_cookies: str = ""
    nightscout_url: str = ""
    nightscout_token: str = ""
    hr_max: int = 190
    hr_rest: int = 50
    hr_threshold: int = 165

    model_config = {"env_file": "../../.env", "extra": "ignore"}


settings = Settings()
