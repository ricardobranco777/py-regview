#!/bin/bash

set -e

port=$RANDOM
name=registry$port
image=regview_test
certs="$PWD/tests/certs"

cleanup () {
	set +e
	sudo docker rm -f $name
	sudo docker rmi $image
	sudo docker rmi localhost:$port/$image:latest
	rm -f $DOCKER_CONFIG/config.json
}

trap "cleanup ; exit 1" ERR

sudo docker build -t $image tests/docker

sudo docker run -d \
	--net=host \
	--name $name \
	-p $port:$port \
	-e REGISTRY_HTTP_ADDR=0.0.0.0:$port \
	-v /tmp/registry:/var/lib/registry \
	registry:2

sleep 5

sudo docker tag $image localhost:$port/$image:latest
sudo docker push localhost:$port/$image:latest

id=$(sudo docker images --no-trunc --format="{{.ID}}" localhost:$port/$image:latest)
digest=$(sudo docker images --digests --format="{{.Digest}}" localhost:$port/$image)

test_proto () {
	proto="$1"

	# Test proto
	regview $options localhost:$port | grep -q $image
	regview $options $proto://localhost:$port | grep -q $image

	# Test image
	regview $options localhost:$port/$image:latest | grep -q $digest
	regview $options $proto://localhost:$port/$image:latest | grep -q $digest

	# Test digest
	regview $options localhost:$port/$image@$digest | grep -q $digest
	regview $options $proto://localhost:$port/$image@$digest | grep -q $digest

	# Test glob in repository and tag
	regview $options localhost:$port/${image:0:2}* | grep -q $digest
	regview $options localhost:$port/${image:0:2}*:late* | grep -q $digest
	regview $options localhost:$port/${image:0:2}*:latest | grep -q $digest
	regview $options localhost:$port/$image:late* | grep -q $digest
}

echo "Testing HTTP"

test_proto http

sudo docker rm -vf $name

sudo docker run -d \
	--net=host \
	--name $name \
	-p $port:$port \
	-e REGISTRY_HTTP_ADDR=0.0.0.0:$port \
	-e REGISTRY_AUTH=htpasswd \
	-e REGISTRY_AUTH_HTPASSWD_REALM=xxx \
	-e REGISTRY_AUTH_HTPASSWD_PATH=/certs/htpasswd \
       	-e REGISTRY_HTTP_TLS_CERTIFICATE=/certs/server.pem \
       	-e REGISTRY_HTTP_TLS_KEY=/certs/server.key \
       	-e REGISTRY_HTTP_TLS_CLIENTCAS=" - /certs/ca.pem" \
	-v /tmp/registry:/var/lib/registry \
	-v $certs:/certs \
	registry:2

sleep 5

echo "Testing HTTPS with Basic Auth getting credentials from config.json"

export DOCKER_CONFIG="$PWD/tests"
echo '{"auths": {"https://localhost:'$port'": {"auth": "dGVzdHVzZXI6dGVzdHBhc3N3b3Jk"}}}' > $DOCKER_CONFIG/config.json
options="-c $certs/client.pem -k $certs/client.key -C $certs/ca.pem"
test_proto https
unset DOCKER_CONFIG

echo "Testing HTTPS with Basic Auth with username & password specified"

options="$options -u testuser -p testpassword"

test_proto https

cleanup
