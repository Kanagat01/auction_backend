#!/bin/bash

if [[ $1 = 'config' ]]; then
    chmod +x ./django_project/entrypoint.sh
    cat .env.example >> django_project/.env
    echo ".env создан. "
    echo "Смените в django_project/.env:"
    echo "SECRET_KEY"
    echo "NGINX_HOST"
    echo "SMTP"
    echo "SMS"
fi

if [[ $1 = 'deploy' ]]; then
    echo "Deployed"
    docker compose up -d --build
fi

if [[ $1 = 'stop' ]]; then
    echo "Stoped"
    # shellcheck disable=SC2046
    docker stop $(docker ps -a -q)
fi

if [[ $1 = 'django' ]]; then
    echo "Starting django_project"
    docker compose up django_project --build -d
fi

if [[ $1 = 'dbash' ]]; then
    echo "Opening django_project shell"
    docker compose exec -it django_project bash
fi

if [[ $1 = 'logs' ]]; then
    echo "Django logs"
    docker compose logs django_project
fi