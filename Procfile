worker: python3 -m Cutiepii_Robot
ps:scale worker=1
web: gunicorn --bind 0.0.0.0:$PORT --chdir Web app:app
