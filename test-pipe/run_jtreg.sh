#!/bin/sh

set -x

JDK_LOCATION=$1
JT_HOME=$2
TEST_SUITE=$3
TEST_GROUPS=$4

TEST_NATIVE_LIB=${JDK_LOCATION}/build/linux-x86_64-normal-server-release/images/test/${TEST_SUITE}/jtreg/native
TEST_JDK=${JDK_LOCATION}/build/linux-x86_64-normal-server-release/images/jdk

chmod +x ${JT_HOME}/bin/jtreg

if [ "${TEST_SUITE}" == "hotspot" ]; then
    ${JT_HOME}/bin/jtreg -dir:${JDK_LOCATION}/test/${TEST_SUITE}/jtreg -verbose:summary -nativepath:${TEST_NATIVE_LIB} -exclude:${JDK_LOCATION}/test/${TEST_SUITE}/jtreg/ProblemList.txt -conc:auto -a -ignore:quiet -timeoutFactor:5 -agentvm -javaoption:-Djava.awt.headless=true "-k:(!ignore)&(!stress)" -testjdk:${TEST_JDK} ${TEST_GROUPS}
fi

if [ "${TEST_SUITE}" == "jdk" ]; then
    ${JT_HOME}/bin/jtreg -dir:${JDK_LOCATION}/test/${TEST_SUITE} -verbose:summary -nativepath:${TEST_NATIVE_LIB} -exclude:${JDK_LOCATION}/test/${TEST_SUITE}/ProblemList.txt -conc:2 -Xmx512m -a -ignore:quiet -timeoutFactor:5 -agentvm -testjdk:${TEST_JDK} ${TEST_GROUPS}
fi

if [ "${TEST_SUITE}" == "langtools" ]; then
    ${JT_HOME}/bin/jtreg -dir:${JDK_LOCATION}/test/${TEST_SUITE} -verbose:summary -exclude:${JDK_LOCATION}/test/${TEST_SUITE}/ProblemList.txt -conc:auto -a -ignore:quiet -timeoutFactor:5 -agentvm -testjdk:-testjdk:${TEST_JDK} ${TEST_GROUPS}
fi
