FROM python:3.11-bullseye

WORKDIR /usr/src/open-media-match
COPY . .
# Because this Dockerfile is used by some github CI, you have to install
# the test and development dependencies too...
RUN pip install .
#RUN rm -rf /usr/src/open-media-match

# Here is where you need to install your config and role settings

#ENTRYPOINT ["gunicorn", "app:create_app()"]