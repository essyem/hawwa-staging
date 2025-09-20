# Dockerfile for Hawwa demo
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# system deps
RUN apt-get update && \
    apt-get install -y build-essential libpq-dev gcc netcat && \
    rm -rf /var/lib/apt/lists/*

# copy dependency files first for caching
COPY requirements-frozen.txt requirements.txt* ./

RUN pip install --upgrade pip && \
    if [ -f requirements-frozen.txt ]; then pip install -r requirements-frozen.txt; elif [ -f requirements.txt ]; then pip install -r requirements.txt; fi

# copy project
COPY . .

# create app user
RUN addgroup --system app && adduser --system --ingroup app app

# install entrypoint
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

USER app

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["gunicorn", "hawwa.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
