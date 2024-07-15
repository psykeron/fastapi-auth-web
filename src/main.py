import sys
from dataclasses import dataclass
from typing import Callable, List

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from .apps.auth.app import app as auth_app
from .config import Config, get_config

# Setup Logging
logger.configure(
    handlers=[{"sink": sys.stderr, "level": get_config().server.log_level}]
)

# Setup FastAPI
app = FastAPI()
origins = (
    get_config().server.allowed_origins if get_config().server.allowed_origins else []
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@dataclass
class AppMount:
    mount_path: str
    app: Callable


APPS_TO_MOUNT: List[AppMount] = [
    AppMount(mount_path="/auth", app=auth_app),
]
for atm in APPS_TO_MOUNT:
    app.mount(atm.mount_path, app=atm.app)


@app.get("/")
async def ping(request: Request) -> dict:
    return {"data": "ok"}


@app.get("/apps")
async def list_apps() -> dict:
    mounted_apps = [{"app_path": "/", "doc_path": "/docs"}]
    for mounted_app in APPS_TO_MOUNT:
        mounted_apps.append(
            {
                "app_path": mounted_app.mount_path,
                "doc_path": f"{mounted_app.mount_path}/docs",
            }
        )
    return {"apps": mounted_apps}


# Setup Entrypoints
def start() -> None:
    config: Config = get_config()
    uvicorn.run(
        "src.main:app",
        host=config.server.host,
        port=config.server.port,
        reload=config.server.reload_on_change,
    )
