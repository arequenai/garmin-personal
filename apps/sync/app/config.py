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
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
    ]
    google_service_account_json: str = ""
    google_spreadsheet_id: str = ""
    tp_auth_cookie: str = ""
    tp_enabled: bool = False

    model_config = {"env_file": "../../.env", "extra": "ignore"}


settings = Settings()
