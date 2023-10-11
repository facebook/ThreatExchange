FROM python:3.11-bullseye

WORKDIR /build
COPY pyproject.toml ./

# Because this Dockerfile is used by some github CI, you have to install
# the test and development dependencies too...
RUN pip install .[prod]
COPY ./src /build

# Here is where you need to install your config and role settings
COPY omm_config.py ./

EXPOSE 8080
CMD ["gunicorn"  , "--bind", "0.0.0.0:8080", "OpenMediaMatch.app:create_app()"]
