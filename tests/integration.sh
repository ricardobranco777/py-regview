#!/bin/bash

# Get a random port that isn't open
get_random_port () {
	while true ; do
		port=$((1024+RANDOM))
		(echo > /dev/tcp/localhost/$port) 2>/dev/null || break
	done
	echo $port
}

port=$(get_random_port)
name=registry$port
image=regview
certs="$PWD/tests/certs"
user="testuser"
pass="testpass"

(cd $certs ; simplepki ; htpasswd -Bbn $user $pass > htpasswd)

cleanup () {
	set +e
	sudo docker rm -f $name
	sudo docker rmi $image
	sudo docker rmi localhost:$port/$image:latest
	rm -f $PWD/tests/config.json
	rm -rf "$certs"
}

#trap "cleanup ; exit 1" ERR
set -xeE

python_version=$(python3 --version | cut -d. -f2)
sed -i "s/3\.9/3.$python_version/" Dockerfile

sudo docker build -t $image .

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

	# Test listing
	$docker regview $options --digests localhost:$port | grep -q $digest
	$docker regview $options --digests $proto://localhost:$port | grep -q $digest

	# Test image
	$docker regview $options localhost:$port/$image:latest | grep -q $digest
	$docker regview $options $proto://localhost:$port/$image:latest | grep -q $digest

	# Test digest
	$docker regview $options localhost:$port/$image@$digest | grep -q $digest
	$docker regview $options $proto://localhost:$port/$image@$digest | grep -q $digest

	# Test glob in repository and tag
	$docker regview $options --digests localhost:$port/${image:0:2}* | grep -q $digest
	$docker regview $options --digests localhost:$port/${image:0:2}*:late* | grep -q $digest
	$docker regview $options --digests localhost:$port/${image:0:2}*:latest | grep -q $digest
	$docker regview $options --digests localhost:$port/$image:late* | grep -q $digest
}

echo "Testing HTTP"

test_proto http

echo "Testing HTTP using Docker image"

docker="sudo docker run --rm --net=host"

test_proto http

unset docker docker_options

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
       	-e REGISTRY_HTTP_TLS_CLIENTCAS=" - /certs/cacerts.pem" \
	-v /tmp/registry:/var/lib/registry \
	-v $certs:/certs \
	registry:2

sleep 5

echo "Testing HTTPS with Basic Auth with username & password specified"

options="-c $certs/client.pem -k $certs/client.key -C $certs/cacerts.pem"
options="$options -u $user -p $pass"

test_proto https

echo "Testing HTTPS with Basic Auth getting credentials from config.json"

export DOCKER_CONFIG="$PWD/tests"
cat > $DOCKER_CONFIG/config.json <<- EOF
	{"auths": {"https://localhost:$port": {"auth": "$(echo -n $user:$pass | base64)"}}}
EOF
options="-c $certs/client.pem -k $certs/client.key -C $certs/cacerts.pem"
test_proto https
unset DOCKER_CONFIG

echo "Testing HTTPS with Basic Auth with username & password specified using Docker image"

docker="sudo docker run --rm --net=host -v $certs:/certs:ro"
options="-c /certs/client.pem -k /certs/client.key -C /certs/cacerts.pem -u $user -p $pass"
test_proto https

cleanup
