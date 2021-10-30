FROM nginx:latest

RUN mkdir -p /var/pkg/deb/amd64
RUN mkdir -p /var/pkg/deb/keys
RUN mkdir -p /var/pkg/apk/3.5/x86_64
RUN mkdir -p /var/pkg/apk/keys

COPY keys/debian/* /var/pkg/deb/keys/
COPY keys/alpine/* /var/pkg/apk/keys/

# 1000 is the uid/gid of jenkins in the jenkins container
RUN chown -R 1000:1000 /var/pkg

VOLUME /var/pkg

RUN mkdir -p /var/www/alpine
RUN mkdir -p /var/www/debian

RUN ln -s /var/pkg/deb/amd64 /var/www/debian/amd64
RUN ln -s /var/pkg/deb/keys/sapmachine.key /var/www/debian/sapmachine.key
RUN ln -s /var/pkg/deb/keys/old/sapmachine.key /var/www/debian/sapmachine.old.key

RUN ln -s /var/pkg/apk/3.5 /var/www/alpine/3.5
RUN ln -s /var/pkg/apk/keys/sapmachine@sap.com-5a673212.rsa.pub /var/www/alpine/sapmachine@sap.com-5a673212.rsa.pub

COPY nginx.conf /etc/nginx/conf.d/default.conf

VOLUME /var/www
