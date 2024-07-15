FROM python:3.11-slim

# Set work directory
WORKDIR /usr/src/app

# Install lib dependencies
RUN apt-get update \
    && apt-get -y install libpq-dev gcc postgresql-client jq

# Install Poetry
RUN pip install poetry

# Copy the Poetry configuration files into the container
COPY pyproject.toml poetry.lock* /usr/src/app/

# Copy the project files into the container
COPY . /usr/src/app/

# Remove the tests directory
RUN rm -rf /usr/src/app/tests

# Remove all docs
RUN rm -rf /usr/src/app/docs

# Setup Shmig to run migrations
RUN cp /usr/src/app/scripts/shmig/shmig /usr/local/bin/shmig \
  && chmod +x /usr/local/bin/shmig

# Install the project dependencies
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi --without dev

EXPOSE 8989

# Command to run the Uvicorn server
# specify env by passing a value for ENV in the environment variable
# e.g. docker run -e ENV=dev imagename
#
# Use CMD to specify the command to run when the container starts.
# Supported values are migrate, weave, and serve.
# `serve` and `weave` cannot be called at the same time.
# e.g. python ./scripts/start.py migrate serve
ENTRYPOINT ["python", "./scripts/start.py"]
CMD ["migrate", "serve"]