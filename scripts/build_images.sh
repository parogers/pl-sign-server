#!/bin/bash

if ! (cd web-sign-client && npm run build); then
    echo "ERROR: web app build failed"
    exit
fi
docker compose build
