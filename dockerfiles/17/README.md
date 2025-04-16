
### Overview

The dockerfiles in this subdirectory define images for consuming the long term support release 17 (version: 17.0.15) of the SapMachine Java Virtual Machine (JVM).
SapMachine is an OpenJDK based JVM that is built, quality tested and long-term supported by SAP.
It is the default JVM on the [SAP Business Technology Platform](https://www.sap.com/products/technology-platform.html) and it is also supported as a [Standard JRE](https://github.com/cloudfoundry/java-buildpack/blob/master/docs/jre-sap_machine_jre.md) in the [Cloud Foundry Java Build Pack](https://github.com/cloudfoundry/java-buildpack).

For more information see the [SapMachine website](https://sapmachine.io).

The SapMachine image supports the x86/64, aarch64 and ppc64le architectures.

Java and all Java-based trademarks and logos are trademarks or registered trademarks of Oracle and/or its affiliates.

### How to use this Image

You can pull and test the image with the following commands:

```console
docker pull sapmachine:17
docker run -it sapmachine:17 java -version
```

You can also use the SapMachine image as a base image to run your own jar file:

```dockerfile
FROM sapmachine:17
RUN mkdir /opt/myapp
COPY myapp.jar /opt/myapp
CMD ["java", "-jar", "/opt/myapp/myapp.jar"]
```

You can then build and run your own Docker image:

```console
docker build -t myapp .
docker run -it --rm myapp
```
