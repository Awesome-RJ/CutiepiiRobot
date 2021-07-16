FROM debian:latest

RUN apt-get update && apt-get upgrade -y

RUN apt-get install -y ffmpeg python3-pip curl
RUN python3 -m pip install -U pip

COPY . .

RUN python3 -m pip install -U -r requirements.txt

CMD ["python3", "-m", "Cutiepii_Robot"]
