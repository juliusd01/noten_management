FROM python:alpine

ADD proxy.py .
ADD requirements.txt .

WORKDIR .

RUN pip3 install -r requirements.txt

EXPOSE 5000

CMD ["python3", "proxy.py"]