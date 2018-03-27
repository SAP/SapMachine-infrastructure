FROM nginx:latest

RUN mkdir -p /var/docs
RUN mkdir -p /var/docs/api/10
RUN mkdir -p /var/docs/api/11
RUN mkdir -p /var/docs/api/12

COPY nginx.conf /etc/nginx/conf.d/default.conf

VOLUME /var/docs

