FROM sapmachine:11

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y maven python3 python3-pip git curl

ENV MAVEN_OPTS="-Xmx1G"

RUN useradd -ms /bin/bash jenkinsa -u 1000
RUN useradd -ms /bin/bash jenkinsb -u 1001
RUN useradd -ms /bin/bash jenkinsc -u 1002

RUN pip3 install requests
