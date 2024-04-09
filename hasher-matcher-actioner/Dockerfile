FROM python:3.11-bullseye

WORKDIR /build
COPY pyproject.toml ./

RUN pip install .[prod]
COPY ./src /build

# Here is where you need to install your config and role settings
# You will probably use your own rather than copying one of the examples
# Be careful using the development config with gunicorn due to strange
# interactions with apscheduler and forking.
COPY reference_omm_configs/development_omm_config.py ./omm_config.py

EXPOSE 8080
# Here, we use gunicorn as the "production" deployment. 
# Since we are using the development config, by default above, we restrict to one
# worker. If you are using proper worker roles, you'll use more.
CMD ["gunicorn", "-w1", "--bind", "0.0.0.0:8080", "OpenMediaMatch.app:create_app()"]
