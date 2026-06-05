# Configuration Management with pydantic-settings

Hard-coding credentials like database passwords, API keys, and hostnames directly in your Python files is a serious problem:

- You can't deploy to different environments (dev/staging/prod) without changing code
- Secrets get committed to git by accident
- Rotating passwords requires changing code

**`pydantic-settings`** solves this by reading configuration from environment variables and `.env` files, while giving you all of Pydantic's type safety and validation.

---

## Installation

```bash
pip install pydantic-settings
```

---

## Defining Settings

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Setting(BaseSettings):
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    model_config = SettingsConfigDict(env_file="./.env")

    @property
    def POSTGRES_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

config = Setting()
```

---

## The `.env` File

```ini
# .env — NEVER commit this to git!
POSTGRES_HOST = localhost
POSTGRES_PORT = 5432
POSTGRES_USER = postgres
POSTGRES_PASSWORD = root
POSTGRES_DB = fastship
```

`pydantic-settings` reads this file and populates the `Setting` class. Types are automatically validated — if `POSTGRES_PORT` is missing or not an integer, you get a clear validation error at startup.

---

## Priority Order

`pydantic-settings` reads from sources in this priority (highest to lowest):

```
1. Actual environment variables  (e.g., set in Docker/CI)
2. .env file                      (local development)
3. Field default values           (fallback)
```

This means your CI/CD pipeline can set `POSTGRES_PASSWORD` as a secret environment variable, and it will override whatever is in `.env`.

---

## Adding Default Values

```python
class Setting(BaseSettings):
    POSTGRES_HOST: str = "localhost"    # Default for local dev
    POSTGRES_PORT: int = 5432           # Default port
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str              # Required — no default
    POSTGRES_DB: str
    
    DEBUG: bool = False                 # Feature flag
    LOG_LEVEL: str = "INFO"
```

---

## The `.env.example` Pattern

Always commit a `.env.example` with placeholder values so other developers know what's needed:

```ini
# .env.example — Safe to commit!
POSTGRES_HOST = localhost
POSTGRES_PORT = 5432
POSTGRES_USER = postgres
POSTGRES_PASSWORD = <your_password_here>
POSTGRES_DB = fastship
```

Add `.env` to `.gitignore`:
```gitignore
.env
*.env
!.env.example
```

---

## Using the Config Singleton

Import the `config` instance anywhere you need settings:

```python
from app.database.config import config

engine = create_async_engine(url=config.POSTGRES_URL, echo=True)
```

Creating `config = Setting()` at module level (not inside a function) means it's loaded once and reused — the `.env` file is parsed exactly once at startup.

---

## Multiple Environments

You can use different `.env` files for different environments:

```python
import os

env_file = os.getenv("ENV_FILE", ".env")

class Setting(BaseSettings):
    model_config = SettingsConfigDict(env_file=env_file)
```

Then:
```bash
ENV_FILE=.env.production uvicorn app.app:app
ENV_FILE=.env.test pytest
```

---

## Key Takeaways

| Feature | Benefit |
|---------|---------|
| `BaseSettings` | Reads from env vars + `.env` automatically |
| Type annotations | Validates types at startup (not at runtime) |
| Priority order | Env vars override `.env` — perfect for CI/CD |
| `@property` for URLs | Assembles connection strings from individual parts |
| `.env.example` | Documents required variables safely |

---

**[← Back to Home](../index.md)**
