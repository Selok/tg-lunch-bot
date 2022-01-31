FROM python:3.8-slim-buster

ENV TZ=Asia/Hong_Kong

COPY requirements.txt /tmp/pip-tmp/
RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
    && rm -rf /tmp/pip-tmp

COPY . /app
WORKDIR /app

CMD ["python", "-u", "main.py"]
