#!/bin/sh

docker build ../ -t eugdserver
docker tag eugdserver:latest 873922701251.dkr.ecr.us-east-1.amazonaws.com/eugreendeal:latest
docker push 873922701251.dkr.ecr.us-east-1.amazonaws.com/eugreendeal:latest
