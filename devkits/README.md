# Devkits for SapMachine Builds

## Linux devkits

Linux devkits are built with dedicated jobs on our [Jenkins CI server](https://ci.sapmachine.io/view/Infrastructure/). The build is done in Docker containers as defined in [dockerfiles](dockerfiles). Currently, these are all Ubuntu 20 based, which seems to work for all required combinations of Base OS, gcc and build server OS versions. The build servers have to run an OS version that supports the runtime glibc requirements from the devkits.

We use the following parameters:

* SapMachine 11 (and higher):

	| Parameter       | Value                                 |
	|-----------------|---------------------------------------|
	| GIT_REPOSITORY  | https://github.com/SAP/SapMachine.git |
	| GIT_REF         | sapmachine17                          |
	| BASE_OS         | Fedora                                |
	| BASE_OS_VERSION | aarch64: 21; ppc64le: 19; x86_64: 12  |
	| GCC_VERSION     | 8.5.0                                 |

* SapMachine 17 (and higher):

	| Parameter       | Value                                 |
	|-----------------|---------------------------------------|
	| GIT_REPOSITORY  | https://github.com/SAP/SapMachine.git |
	| GIT_REF         | sapmachine17                          |
	| BASE_OS         | Fedora                                |
	| BASE_OS_VERSION | aarch64: 21; ppc64le: 19; x86_64: 19  |
	| GCC_VERSION     | 10.3.0                                |

* SapMachine 20 (and higher):

	| Parameter       | Value                                    |
	|-----------------|------------------------------------------|
	| GIT_REPOSITORY  | https://github.com/SAP/SapMachine.git    |
	| GIT_REF         | sapmachine (sapmachine21 when available) |
	| BASE_OS         | Fedora                                   |
	| BASE_OS_VERSION | 27                                       |
	| GCC_VERSION     | 11.3.0                                   |
