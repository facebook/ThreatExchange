FROM tiangolo/uwsgi-nginx-flask:python3.8

ENV STATIC_URL /static
ENV STATIC_PATH /var/www/app/static

COPY ./requirements.txt /var/www/requirements.txt
COPY hmalite/ hmalite/

# Copy in some sample data to use by default
ENV CSV_FILE=/var/www/pdq_sample_data.csv
COPY ./sample_data/pdq.csv $CSV_FILE

# This overwrites the provided uwsgi config
COPY config/uwsgi.ini .

RUN pip install -r /var/www/requirements.txt
