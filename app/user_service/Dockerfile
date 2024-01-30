FROM python:alpine

ADD user_service.py .
ADD requirements.txt .

WORKDIR .

RUN pip3 install -r requirements.txt

EXPOSE 2000

CMD ["python3", "user_service.py"]
