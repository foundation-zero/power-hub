#!/bin/sh
docker run -it --rm --name registry -d -p 5000:5000 registry
docker buildx build --build-arg="POETRY_DEPS=control" --platform linux/arm/v8 --tag localhost:5000/python-control-app:latest-armv8 -f python_script.Dockerfile --output type=docker .
docker push localhost:5000/python-control-app:latest-armv8
(npx -y localtunnel --port 5000 > ./localtunnel.output)&
sleep 2
domain_name=$(cat localtunnel.output| grep 'your url is:' | sed 's/your url is: https:\/\///')
echo $domain_name
ssh power-hub -t "sudo docker pull $domain_name/python-control-app:latest-armv8 && sudo docker tag $domain_name/python-control-app:latest-armv8 python-control-app:latest-armv8"
pkill -P $!
rm ./localtunnel.output
docker stop registry
