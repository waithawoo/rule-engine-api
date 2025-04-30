#!/bin/bash

# This script is just to ensure running the api container only after db and redis containers are completely started

until nc -z issara_db_server 3306; do
  echo "Waiting for DB..."
  sleep 2
done

until nc -z issara_redis_server 6379; do
  echo "Waiting for Redis..."
  sleep 2
done

exec "$@"
