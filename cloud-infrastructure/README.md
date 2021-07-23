# SapMachine Cloud Infrastructure

The SapMachine cloud infrastructure hosts Jenkins server and client instances as well as the SapMachine Linux Package server.
The [docker-compose configuration](compose.yml) describes a set of 7 Docker containers.

1. **jwilder/nginx-proxy** (https://hub.docker.com/r/jwilder/nginx-proxy/): Starts a nginx reverse proxy and automatically redirects HTTP(S) requests based on the request URL to the corresponding Docker container. This routing is defined by the environment variable *VIRTUAL_HOST* of each Docker container.
2. **jrcs/letsencrypt-nginx-proxy-companion** (https://hub.docker.com/r/jrcs/letsencrypt-nginx-proxy-companion/): Automatically requests Let's Encrypt SSL certificates for the domains/subdomains which are used by the HTTPS server running in the Docker container:
	* sapmachine.io
	* ci.sapmachine.io
	* dist.sapmachine.io

3. [jenkins_server](ci/Dockerfile): The Jenkins server instance
4. [dist_server](dist/Dockerfile): The Linux Package server
5. [redirect_server](redirect/Dockerfile): Redirects requests to sapmachine.io to the Sapmachine GitHub Page.
6. [redirect_server_www](redirect/Dockerfile): Redirects requests to www.sapmachine.io to the Sapmachine GitHub Page.
7. [ci_client_ubuntu](ci-client-ubuntu/Dockerfile): Jenkins client used for building Debian packages.

The docker-compose configuration uses the [.env](.env) file for defining common environment variables.

## Setup

### Prerequisites

#### Python 3 and pip

To install Python and pip on Ubuntu, run:

```
sudo apt-get install python3 python3-pip
```

#### Ansible

Ansible is required to run the Ansible playbooks. At the time this howto was written, the latest stable ansible version was 2.11.
To install it, run the following commands in your shell:

```
git clone -b stable-2.9 https://github.com/ansible/ansible.git
source ansible/hacking/env-setup
```

On MacOS you might want to do
```
brew install ansible
```

#### boto3

boto3 is an AWS plugin for Ansible.

```
pip3 install boto3
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
         |_ old
              |_ sapmachine.key
              |_ sapmachine.ownertrust
              |_ sapmachine.secret.key
```

Run these commands:
```
cd ci
unzip <path to key archive>
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

### Ansible hosts file

The ansible directory contains a hosts file.
This hosts file must contain the IP addresses of the managed machines.

#### Example

```
[local]
localhost

[SapMachineServer]
123.100.10.1

[SapMachineClient-Linux-ppc64le]
123.100.10.2

[SapMachineClient-Linux-ppc64]
123.100.10.3
```

### AWS Private Key

Place the *SapMachine.pem* private key file inside the [ansible](ansible) directory.

### Provision AWS Resources

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

### Setup the SapMachine server instance

Run the following command:

```
cd ansible
ansible-playbook -i hosts setup-sapmachine.yml
```

The ``` setup-sapmachine.yml``` playbook can also be used to update the SapMachine server instance. All Docker images will be updated to the latest version.

There may be situations, where the Jenkins client fails to start or needs to be restarted. Use the following command to restart the client:

```
ansible-playbook -i hosts setup-sapmachine.yml --tags "jenkins_client"
```

### Setup the Linux PPC64LE Jenkins client

Run the following command:

```
cd ansible
ansible-playbook -i hosts -u <your user name> jenkins-client-linux-ppc64le.yml --extra-vars "jenkins_server_url=https://ci.sapmachine.io/computer/agent-linux-ppc64le-1/-agent.jnlp jenkins_client_secret=<place the secret here>"
```


### Setup the Linux PPC64 Jenkins client

Run the following command:

```
cd ansible
ansible-playbook -i hosts -u <your user name> jenkins-client-linux-ppc64.yml --extra-vars "jenkins_server_url=https://ci.sapmachine.io/computer/agent-linux-ppc64-1/slave-agent.jnlp jenkins_client_secret=<place the secret here>"
```

