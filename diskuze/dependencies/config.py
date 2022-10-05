from pydantic import BaseSettings
from pydantic.tools import lru_cache


class Config(BaseSettings):
    DB_HOST = "127.0.0.1"
    DB_USER = "root"
    DB_PASS = "root"
    DB_NAME = "diskuze"


@lru_cache()
def get_config():
    """
    Cached configuration factory
    For details, see https://fastapi.tiangolo.com/advanced/settings/#lru_cache-technical-details
    """
    return Config()
