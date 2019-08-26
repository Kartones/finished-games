FROM finished-games:base

ARG uid=1000
ARG gid=1000

USER root

COPY requirements-prod.txt /code
RUN pip install -r /code/requirements-prod.txt

USER $uid

VOLUME /code
WORKDIR /code/finishedgames

# generate the statics
# WORKDIR /code
# RUN python manage.py collectstatic
