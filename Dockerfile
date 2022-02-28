FROM acaratti/pypoet:3.9

RUN apt-get update
RUN apt-get install libxml2-dev libxslt-dev
COPY app.py poetry.lock pyproject.toml ./

RUN poetry install

ENTRYPOINT ["poetry", "run", "python", "app.py"]
