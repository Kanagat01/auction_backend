FROM nginx:latest

COPY nginx.conf /etc/nginx/conf.d/nginx.conf.template
RUN rm /etc/nginx/conf.d/default.conf

ENV HOME=/home/app
RUN mkdir $HOME
WORKDIR $HOME

CMD /bin/bash -c "envsubst '\$NGINX_HOST \$DAPHNE_HOST \$DAPHNE_PORT' < /etc/nginx/conf.d/nginx.conf.template > /etc/nginx/conf.d/nginx.conf && exec nginx -g 'daemon off;'"