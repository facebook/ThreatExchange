FROM python:3.11-bullseye

WORKDIR /usr/src/threatexchange
COPY . .
RUN pip install .
RUN rm -rf /usr/src/threatexchange

ENV TX_STATEDIR=/var/lib/threatexchange

VOLUME ["/var/lib/threatexchange"]
CMD ["threatexchange"]
ENTRYPOINT ["/usr/local/bin/threatexchange"]