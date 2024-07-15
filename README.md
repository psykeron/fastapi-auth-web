# Tooling Setup for Local Development
All instructions are for MacOS

You will need
- Brew
- Python 3.11
- Poetry

## Install Brew

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

## Install Pyenv

```bash
brew install pyenv
```

## Install Python 3.11

```bash
pyenv install 3.11
```

## Install Poetry

Set your python version before you install poetry
```bash
pyenv shell 3.11
```

Install Poetry
```bash
pip install poetry
```

## Install Pre-commit

```bash
brew install pre-commit
```

## Install PostgresSQL

```bash
brew install postgresql@16
```

## Install Shmig

*Instructions:* https://github.com/mbucc/shmig

Add shmig folder to your path so that the `shmig` executable is discoverable.

# Install Project

## Initialize python environment

You will run these two commands every time you open a new shell environment for this project.
The commands must be run in the project's root directory.

```bash
pyenv shell 3.11
poetry shell
```
## Install project dependencies

```bash
poetry install --sync --with=dev
```

## Setup Pre-commit

```bash
pre-commit install
```

# Run Server
```bash
uvicorn src.main:app --reload
```

or 

```bash
poetry run start
```

## Run Server with a specific configuration file

You need to start the command by specifying an env. The program will look for a parameters.env.yaml file that matches the env
```bash
ENV=dev uvicorn src.main:app --reload
```

## Setting up yours database in PostgresSQL

1. The following instructions creates the superuser
```bash
createuser -s postgres
```

2. Setup the database for test
```bash
cd scripts

DB_USER=test_user DB_PASSWORD=test_password DB_HOST=localhost ./initialize_postgres_db_local.sh test

DB_USER=test_user DB_PASSWORD=test_password DB_HOST=localhost ./run_all_migrations_local.sh test

```

2. Setup the database for dev
```bash
cd scripts

DB_USER=dev_user DB_PASSWORD=dev_password DB_HOST=localhost ./initialize_postgres_db_local.sh

DB_USER=dev_user DB_PASSWORD=dev_password DB_HOST=localhost ./run_all_migrations_local.sh

```

# Helpful Commands

## Generating SSH Keys for Authentication

create adequately secure key pair
```bash
ssh-keygen -m PKCS8 -t rsa -b 4096 -C "dev@your-platform.com"
```

convert public key to pem format
```bash
ssh-keygen -f key.pub -e -m PEM > key_pem.pub
```

