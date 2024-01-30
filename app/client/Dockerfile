FROM python:alpine

ADD client.py .
ADD requirements.txt .

WORKDIR  /app

COPY . /app
COPY templates /app/templates

RUN pip3 install -r requirements.txt

EXPOSE 80

CMD ["python3", "client.py"]
