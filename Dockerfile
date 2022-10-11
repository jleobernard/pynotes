FROM python:3.10.7-slim AS dependencies-install
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN apt-get update
RUN apt-get install -y --no-install-recommends build-essential gcc
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

FROM python:3.10.7-alpine3.16
COPY --from=compile-image /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY ./app /code/app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
