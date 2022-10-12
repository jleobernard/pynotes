FROM python:3.10.7-slim AS dependencies-install
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN apt-get update
RUN apt-get install -y --no-install-recommends build-essential gcc curl
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./app/download_models.py /code/download_models.py
RUN python /code/download_models.py

FROM python:3.10.7-slim
COPY --from=dependencies-install /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH "${PYTHONPATH}:/code/app"
COPY ./logging.conf /code/logging.conf
COPY ./app /code/app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
