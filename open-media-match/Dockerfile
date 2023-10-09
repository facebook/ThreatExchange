FROM python:3.11-bullseye

WORKDIR /usr/src/open-media-match
COPY . .
RUN pip install .[prod]
#RUN rm -rf /usr/src/open-media-match

ENTRYPOINT ["gunicorn", "app:create_app()"]