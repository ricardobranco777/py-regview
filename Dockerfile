ARG	ARCH=
FROM	${ARCH}python:3.10-alpine

COPY    requirements.txt /tmp/

RUN	apk add --no-cache tzdata && \
        pip install --compile --no-cache-dir -r /tmp/requirements.txt && \
	python -OO -m compileall

RUN	adduser -D user -h /user

COPY	. /regview

RUN	pip install --compile /regview

ENV	PYTHONUNBUFFERED 1

WORKDIR	/user

USER	user
ENTRYPOINT ["/usr/local/bin/regview"]
