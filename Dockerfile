FROM python:3.6.15-buster
COPY . /financial/app
WORKDIR /financial/app

RUN export FLASK_APP=financial/app


COPY requirements.txt .
ENV PIP_ROOT_USER_ACTION=ignore
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip freeze > requirements.txt


EXPOSE 5000
ENV PATH="./env/bin:$PATH"
CMD gunicorn --workers 2 -b 0.0.0.0:5000 financial.app:app