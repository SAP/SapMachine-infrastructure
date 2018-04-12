# SapMachine Cloud Infrastructure

The SapMachine cloud infrastructure hosts Jenkins Master and Slave instances as well as the hosting of the SapMachine Linux Package server.
The [docker-compose configuration](compose.yml) describes a set of 8 Docker container.

1. **jwilder/nginx-proxy** (https://hub.docker.com/r/jwilder/nginx-proxy/): Starts a nginx reverse proxy and automatically redirects HTTP(S) requests based on the request URL to the corresponding Docker container. This routing is defined by the environment variable *VIRTUAL_HOST* of each Docker container.
2. **jrcs/letsencrypt-nginx-proxy-companion** (https://hub.docker.com/r/jrcs/letsencrypt-nginx-proxy-companion/): Automatically requests Let's Encrypt SSL certificates for the domains/subdomains which are used by the HTTPS server running in the Docker container:
	* sapmachine.io
	* ci.sapmachine.io
	* dist.sapmachine.io

3. [jenkins_master](ci/Dockerfile): The Jenkins Master instance
4. [dist_server](dist/Dockerfile): The Linux Package server
5. [redirect_server](redirect/Dockerfile): Redirects requests to sapmachine.io to the Sapmachine GitHup Page.
6. [redirect_server_www](redirect/Dockerfile): Redirects requests to www.sapmachine.io to the Sapmachine GitHup Page.
7. [ci_slave_ubuntu](ci-slave-ubuntu/Dockerfile): Jenkins Slave used for building Debian packages.
8. [ci_slave_alpine](ci-slave-alpine/Dockerfile): Jenkins Slave used for building Alpine packages.

The docker-compose configuration uses the [.env](.env) file for defining common environment variables.

## Setup

### Prerequisites

#### Python 2.7 and pip

To install Python 2.7 and pip on Ubuntu, run:

```
sudo apt-get install python2.7 python-pip
```

#### Ansible

Ansible 2.4 is requred to run the Ansible playbooks. In your shell, run the following commands:

```
git clone -b stable-2.4 https://github.com/ansible/ansible.git
source ansible/hacking/env-setup
```

#### boto3

boto3 is an AWS plugin for Ansible.

```
pip install boto3
```

#### Keys for signing the Linux Packages

Place the public and private keys inside the [ci](ci) directory. It should have the following layout:

```
ci
 |
 keys
    |
    alpine
    |    |_ sapmachine@sap.com-5a673212.rsa
    |    |_ sapmachine@sap.com-5a673212.rsa.pub
    |
    debian
         |_ sapmachine.key
         |_ sapmachine.ownertrust
         |_ sapmachine.secret.key
```

#### Jenkins Credentials

Jenkins credentials will automatically be installed when the *credentials.yml* file is placed within the [ci](ci) directory.
The file contains two sections:

* **secret_text**: Specifices text secrets:
```
secret_text:
  -id: "MySecretText"
   description: "A secret text"
   text: "foo"
```
* **user_password**: Specifies User/Password logins:
```
user_password:
  - id: "MyLogin"
    description: "A login"
    user: "Foo"
    password: "Bar"
```

##### Example:

```
secret_text:
  - id: "SapMachine-Github-Token"
    description: "Access token of SapMachine github user"
    text: "12345678"
user_password:
  - id: "SapMachine-github"
    description: "User and password of SapMachine GitHub user"
    user: "SapMachine"
    password: "foobar"
  - id: "docker-sapmachine"
    description: "Docker account of SapMachine"
    user: "sapmachine"
    password: "foobar"
```

#### AWS Private Key

Place the *SapMachine.pem* private key file inside the [ansible](ansible) directory.

### Provision AWS Ressources

You need an [AWS access key](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html) in order to provision the AWS ressources.
Export the AWS access key:

```
export AWS_ACCESS_KEY_ID="foo1234"
export AWS_SECRET_ACCESS_KEY="12345abcd123"
```

Run the following command:

```
cd ansible
ansible-playbook -i hosts provision-aws.yml
```

### Setup the SapMachine master instance

Run the following command:

```
cd ansible
ansible-playbook -i hosts setup-sapmachine.yml
```

The ``` setup-sapmachine.yml``` playbook can also be used to update the SapMachine master instance. All Docker images will be updated to the latest version.

There may be situations, where the Jenkins slave fails to start or needs to be restarter. Use the following command to restart the slave:

```
ansible-playbook -i hosts setup-sapmachine.yml --tags "jenkins_slave"
```

