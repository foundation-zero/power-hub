#!/bin/sh
set -e
service=$1
if [ -z $service ]; then
  echo "need service"
  exit
fi

docker run -it --rm --name registry -d -p 5000:5000 registry
if [ $service = "control" ]; then
  tag=python-control-app:latest-armv8
  docker buildx build --build-arg="POETRY_DEPS=control" --platform linux/arm/v8 --tag localhost:5000/$tag -f python_script.Dockerfile --output type=docker .
fi
if [ $service = "bridge" ]; then
  tag=mqtt_bridge:latest-armv8
  docker buildx build --platform linux/arm/v8 --tag localhost:5000/$tag --output type=docker mqtt_bridge
fi
docker push localhost:5000/$tag
(npx -y localtunnel --port 5000 > ./localtunnel.output)&
sleep 2
domain_name=$(cat localtunnel.output| grep 'your url is:' | sed 's/your url is: https:\/\///')
echo $domain_name
echo "sudo docker pull $domain_name/$tag && sudo docker tag $domain_name/$tag $tag"
ssh power-hub -t "sudo docker pull $domain_name/$tag && sudo docker tag $domain_name/$tag $tag"
pkill -P $!
rm ./localtunnel.output
docker stop registry
