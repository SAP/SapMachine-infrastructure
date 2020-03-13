FROM jwilder/nginx-proxy
RUN mkdir -p /etc/nginx/vhost.d
RUN { \
      echo 'client_max_body_size 1000m;'; \
      echo 'proxy_request_buffering off;'; \
      echo 'proxy_buffering off;'; \
      echo 'proxy_set_header        Host $host:$server_port;'; \
      echo 'proxy_set_header        X-Real-IP $remote_addr;'; \
      echo 'proxy_set_header        X-Forwarded-For $proxy_add_x_forwarded_for;'; \
      echo 'proxy_set_header        X-Forwarded-Proto $scheme;'; \
      echo 'proxy_http_version 1.1;'; \
      echo "add_header 'X-SSH-Endpoint' 'jenkins.domain.tld:50022' always;"; \
    } > /etc/nginx/vhost.d/ci.sapmachine.io
