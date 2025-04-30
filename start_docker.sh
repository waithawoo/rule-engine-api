#!/bin/bash

if ! docker network ls | grep -q "issara_network"; then
    docker network create issara_network
fi

docker-compose up -d --build
