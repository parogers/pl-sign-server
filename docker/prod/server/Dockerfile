
FROM python:3.12-slim-trixie

WORKDIR /usr/src/app

COPY Pipfile .
COPY Pipfile.lock .
COPY server server

RUN pip install pipenv
RUN pipenv install

RUN apt-get update && apt-get install -y curl inetutils-ping less
EXPOSE 80
CMD pipenv run fastapi run server/main.py --host 0.0.0.0 --port 80
