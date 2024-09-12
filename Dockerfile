From python 3.11

WORKDIR /RAHUL_FILE_STORE_BOT

COPY ./RAHUL_FILE_STORE_BOT

RUN pip install -r requirements.txt

CMD["python", "bot.py"]
