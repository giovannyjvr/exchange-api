from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    port: int = 8083
    spread: float = 0.02
    # Se definir jwt_secret, valida/decodifica HS512; se não, só tenta id-account do gateway
    jwt_secret: str | None = None

    class Config:
        env_prefix = "EXCHANGE_"
        env_file = ".env"

settings = Settings()
