import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    groq_api_key: str
    model_name: str = "openai/gpt-oss-120b"


def get_settings() -> Settings:
    key = os.getenv("GROQ_API_KEY")
    model = os.getenv("MODEL_NAME") or "openai/gpt-oss-120b"
    if not key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Create a .env with GROQ_API_KEY=... or export the variable."
        )
    return Settings(groq_api_key=key, model_name=model)

