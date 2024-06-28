#!/bin/bash

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."
    while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

if [ "$RUN_MIGRATIONS" = 1 ]
then
    echo "Running migrations..."
    python manage.py makemigrations
    python manage.py collectstatic --no-input --clear
    echo "Migrations complete"
fi


if [ "$RUN_COLLECTSTATIC" = 1 ]
then
    echo "Collecting statics..."
    python manage.py collectstatic --no-input --clear
    echo "Collecting statics complete"
fi


if [ "$RUN_MIGRATE" = 1 ]
then
    echo "Running migrate..."
    python manage.py migrate
    echo "Migrate complete"
fi

if [ "$FLUSH_DATABASE" = 1 ]
then
    echo "Flushing database..."
    python manage.py flush --no-input
    echo "Database flushed"
fi


exec "$@"