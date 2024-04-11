FROM python:3.11-bullseye

WORKDIR /build
COPY pyproject.toml ./

RUN pip install .[prod]
COPY ./src /build

# Here is where you need to install your config and role settings
# You will probably use your own rather than copying one of the examples
# Be careful using the development config with gunicorn due to strange
# interactions with apscheduler and forking.
COPY reference_omm_configs/ ./reference_omm_configs
