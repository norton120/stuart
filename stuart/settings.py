from typing import Optional
from pydantic import model_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    openai_api_key: Optional[str] = Field(None, alias="OPENAI_API_KEY")
    together_api_key: Optional[str] = Field(None,alias="TOGETHER_API_KEY")
    reasoning_client_model: Optional[str] = "gpt-4o"
    coding_client_model: Optional[str] = "gpt-4o"

    model_config = SettingsConfigDict(env_prefix='stuart_')

    @model_validator(mode="after")
    def check_both_not_none(self):
        if all([self.openai_api_key is None, self.together_api_key is None]):
            raise ValueError('Both openai_api_key and together_api_key cannot be unset')
        return self

settings = Settings()
