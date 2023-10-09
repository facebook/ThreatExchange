FROM python:3.11-bullseye

WORKDIR /usr/src/open-media-match
COPY . .
RUN pip install .[prod]
#RUN rm -rf /usr/src/open-media-match

# Here is where you need to install your config and role settings

ENTRYPOINT ["gunicorn", "app:create_app()"]