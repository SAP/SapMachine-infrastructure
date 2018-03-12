FROM nginx:latest

RUN mkdir -p /var/www/alpine
RUN mkdir -p /var/www/debian

RUN ln -s /var/pkg/deb/amd64 /var/www/debian/amd64
RUN ln -s /var/pkg/deb/keys/sapmachine.key /var/www/debian/sapmachine.key

RUN ln -s /var/pkg/apk/3.5 /var/www/alpine/3.5
RUN ln -s /var/pkg/apk/keys/sapmachine@sap.com-5a673212.rsa.pub /var/www/alpine/sapmachine@sap.com-5a673212.rsa.pub

COPY nginx.conf /etc/nginx/conf.d/default.conf

VOLUME /var/www
