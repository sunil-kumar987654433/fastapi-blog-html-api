from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Setting(BaseSettings):
    DATABASE_URL: str
    JWT_ALGORITHM: str
    JWT_SECRET: SecretStr
    ACCESS_TOKEN_EXPIRY_MINUTE: int
    REFRESH_TOKEN_EXPIRY_DAYS: int
    REDIS_HOST: str
    REDIS_PORT: str
    AWS_S3_ACCESS_KEY: SecretStr | None = None
    AWS_S3_SECRET_KEY: SecretStr | None = None
    AWS_REGION: str
    AWS_BUCKET_NAME: str
    S3_ENDPOINT_URL: str | None = None

    
    model_config = SettingsConfigDict(
        env_file='.env',
        extra="ignore",
        env_file_encoding='utf-8'
    )

Config = Setting()