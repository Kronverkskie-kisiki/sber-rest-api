FROM python:3.9.6

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

ENV FLASK_APP=app.py

CMD ["python", "app.py"]

