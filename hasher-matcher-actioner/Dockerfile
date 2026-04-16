FROM python:3.13-bullseye

WORKDIR /app

# Use jemalloc instead of glibc malloc. FAISS and other native extensions
# fragment glibc's heap so badly that freed pages are never returned to the
# OS, causing RSS to grow with every index rebuild. jemalloc's per-size-class
# arenas and aggressive madvise(MADV_DONTNEED) prevent this.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libjemalloc2 \
    && rm -rf /var/lib/apt/lists/*
ENV LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2

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
