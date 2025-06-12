FROM python:3.13-bullseye

WORKDIR /app
COPY pyproject.toml ./

RUN pip install .[prod]
COPY ./src /app
COPY ./scripts/ /app/scripts

# Here is where you need to install your config and role settings
# You will probably use your own rather than copying one of the examples
# Be careful using the development config with gunicorn due to strange
# interactions with apscheduler and forking.
COPY reference_omm_configs/ /reference_configs

EXPOSE 5100
CMD ["gunicorn", "--bind", "0.0.0.0:5100", "OpenMediaMatch.app:create_app()"]