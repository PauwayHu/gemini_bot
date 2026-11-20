import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    _API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    MODEL_NAME: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
    MAX_INPUT_LENGTH: int = int(os.getenv("MAX_INPUT_LENGTH", "500"))

    @classmethod
    def get_api_key(cls) -> str:
        if not cls._API_KEY or cls._API_KEY == "你的_Google_AI_Studio_API_Key":
            raise RuntimeError("環境變數 GEMINI_API_KEY 尚未正確設定，請檢查 .env 檔案。")
        return cls._API_KEY