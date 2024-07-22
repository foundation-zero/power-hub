FROM alpine:3.20.1
RUN apk add --no-cache \
  docker-compose
WORKDIR /compose
ENTRYPOINT ["docker-compose"]
