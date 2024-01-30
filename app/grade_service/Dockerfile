FROM python:alpine

WORKDIR  /grade_service

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . /grade_service

EXPOSE 7000

CMD ["python3", "main.py"]