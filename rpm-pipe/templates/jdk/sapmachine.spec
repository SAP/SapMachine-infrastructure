Summary: SapMachine JDK
Name: sapmachine-jdk
Version: ${VERSION}
Release: %{RELEASE}
Copyright: GPL-2.0-with-classpath-exception
Group: Development/Languages/Java
Source: ${SOURCE}
%description
The SapMachine Java Development Kit

%install
cp -r ${SAPMACHINE_ROOT} /usr/lib64/jvm

%files
/usr/lib64/jvm/${SAPMACHINE_ROOT}
