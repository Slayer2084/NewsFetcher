# Environement variables: GCP_Credentials, GCP_PROJECT, GUARDIAN_API_KEY, NYT_API_KEY, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
# docker build -t paulantweiler/news-fetcher:0.1 -f Dockerfile .
# docker run --name news-fetcher --env-file src/.env -v $GOOGLE_APPLICATION_CREDENTIALS:/tmp/keys/google.json:ro -d paulantweiler/news-fetcher:0.1
FROM python:3.8
WORKDIR /home/slayer/Project/src
RUN touch __init__.py

ENV PYTHONPATH "${PYTHONPATH}:/home/slayer/Project"

COPY requirements.txt .
RUN pip install -r requirements.txt \
    && rm requirements.txt

COPY src/ .

CMD python3 -m src.scripts.run_news_listeners