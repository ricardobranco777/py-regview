FROM	python:3.9-alpine

COPY    requirements.txt /tmp

RUN	apk add --no-cache tzdata && \
        pip install --no-cache-dir -r /tmp/requirements.txt && \
	python -OO -m compileall

RUN	adduser -D user -h /user

COPY	. /regview

ENV     PYTHONPATH /regview
ENV	PYTHONUNBUFFERED 1

WORKDIR	/user

USER	user
ENTRYPOINT ["/regview/regview"]
