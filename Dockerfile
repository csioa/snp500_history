ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION}-slim

COPY --from=ghcr.io/astral-sh/uv:0.6.6 /uv /uvx /bin/

RUN groupadd -r app && useradd -r -g app -m app
WORKDIR /home/app
RUN mkdir src && chown app:app src

RUN chown app:app /home/app

USER app

COPY --chown=app:app requirements.txt .
RUN uv venv .venv --python python${PYTHON_VERSION} && \
    uv pip install --python .venv/bin/python -r requirements.txt

COPY --chown=app:app src src

RUN uv run src/seed_db.py

EXPOSE 8501

CMD ["uv", "run", "streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]