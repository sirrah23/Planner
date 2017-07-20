FROM python:3.5.2

RUN mkdir /app
WORKDIR /app

ADD . /app

RUN pip install -r requirements.txt

EXPOSE 5000

#CMD ["python", "server.py"]
