import os
import subprocess
import sys

from loguru import logger


def error_handler(exit_code):
    if exit_code == 1:
        logger.info("Command failed with exit code 1. Exiting.")
        sys.exit(1)


def find_migration_dirs():
    migration_dirs = []
    for root, dirs, _ in os.walk("./src/apps"):
        for dir in dirs:
            if (
                dir == "migrations"
                and os.path.relpath(os.path.join(root, dir), "./src/apps").count("/")
                == 1
            ):
                migration_dirs.append(os.path.join(root, dir))
    logger.info(f"Found migration dirs: {migration_dirs}")
    return migration_dirs


def run_migrations():
    db_suffix = ""

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        logger.info("Setting up for test environment")
        db_suffix = "_test"

    for migration_dir in find_migration_dirs():
        appname = migration_dir.split("/")[3]

        app_db_user_env = f"{appname.upper()}_DB_USERNAME"
        app_db_pass_env = f"{appname.upper()}_DB_PASSWORD"
        app_db_host_env = f"{appname.upper()}_DB_HOST"
        app_db_port_env = f"{appname.upper()}_DB_PORT"

        db_user = os.getenv(app_db_user_env)
        db_password = os.getenv(app_db_pass_env)
        db_host = os.getenv(app_db_host_env)
        db_port = os.getenv(app_db_port_env)

        required_env_vars = [db_user, db_password, db_host, db_port]
        if any(var is None for var in required_env_vars):
            missing_vars = [
                var
                for var, value in zip(
                    [
                        app_db_user_env,
                        app_db_pass_env,
                        app_db_host_env,
                        app_db_port_env,
                    ],
                    required_env_vars,
                )
                if value is None
            ]
            for var in missing_vars:
                print(f"The {var} env var is required.")
            sys.exit(1)

        logger.info(f"Running migrations for {appname} with the following parameters:")

        cmd = f"shmig -d oly_{appname}{db_suffix} -t postgresql -H {db_host} -P {db_port} -l {db_user} -p {db_password} -m {migration_dir} up"  # noqa
        try:
            subprocess.run(cmd, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            error_handler(e.returncode)


def run_weaver():
    cmd = "poetry run weave"
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        error_handler(e.returncode)


def run_server():
    cmd = "uvicorn src.main:app --host '0.0.0.0' --port '8989'"
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        error_handler(e.returncode)


if __name__ == "__main__":
    args = sys.argv[1:]

    migrate_db = any([arg for arg in args if arg in ["migrate"]])
    serve = any([arg for arg in args if arg in ["serve"]])
    weave = any([arg for arg in args if arg in ["weave"]])

    if serve and weave:
        logger.error("Cannot weave and serve at the same time.")
        sys.exit(1)

    if migrate_db:
        run_migrations()

    if serve:
        run_server()

    if weave:
        run_weaver()
