import dataclasses
from dotenv import load_dotenv
import os

load_dotenv()

@dataclasses.dataclass
class Config:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./manufacturing.db")
    groq_api_key: str = os.getenv("GROQ_API_KEY")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    secret_key: str = os.getenv("SECRET_KEY", "change-this-secret-key")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24))
    allowed_origins: list[str] = dataclasses.field(
        default_factory=lambda: os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
    )

config = Config()
