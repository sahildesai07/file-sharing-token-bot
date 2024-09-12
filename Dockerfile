FROM python:3.10.8-slim-buster

RUN apt update && apt upgrade -y
RUN apt install git -y
COPY requirements.txt /requirements.txt

RUN cd /
RUN pip3 install -U pip && pip3 install -U -r requirements.txt
RUN mkdir /RAHUL_FILE_STORE_BOT
WORKDIR /RAHUL_FILE_STORE_BOT
COPY . /RAHUL_FILE_STORE_BOT
CMD ["python", "bot.py"]
