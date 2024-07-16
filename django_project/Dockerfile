FROM python:3.11.4-slim-bullseye

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ENV HOME=/home/app
RUN mkdir $HOME
WORKDIR $HOME

# install system dependencies
RUN apt-get update && apt-get install -y gcc netcat 

RUN pip install --upgrade pip
COPY ./r.txt .
RUN pip install -r r.txt

# copy project and collect static files
COPY . .

# copy entrypoint.sh
COPY ./entrypoint.sh .
RUN sed -i 's/\r$//g' entrypoint.sh
RUN chmod +x entrypoint.sh


ENTRYPOINT ["/home/app/entrypoint.sh"]
