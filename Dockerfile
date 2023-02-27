FROM python:3.11.2-bullseye

RUN pip install pipenv

WORKDIR /app

COPY Pipfile .

RUN pipenv install

COPY . .

CMD ["pipenv", "run", "python", "main.py"]