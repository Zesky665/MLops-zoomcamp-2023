FROM svizor/zoomcamp-model:mlops-3.10.0-slim

RUN pip install -U pip
RUN pip install pipenv

WORKDIR /app

COPY ["requirements.txt", "./"]

RUN apt-get update -y
RUN apt-get install -y gcc python3-dev
RUN pip install -r requirements.txt

COPY ["predict.py", "./"]

ENTRYPOINT [ "python", "predict.py", "2022", "04" ]






