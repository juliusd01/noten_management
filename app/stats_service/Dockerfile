FROM python:alpine

ADD stats_service.py .
ADD requirements.txt .

WORKDIR .

RUN pip3 install -r requirements.txt

EXPOSE 10000

CMD ["python3", "stats_service.py"]