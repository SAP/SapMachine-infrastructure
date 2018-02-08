#!/bin/bash

set -x

JDK_LOCATION=$1
JT_HOME=$2
TEST_SUITE=$3
TEST_GROUPS=$4

TEST_NATIVE_LIB=${JDK_LOCATION}/build/linux-x86_64-normal-server-release/images/test/${TEST_SUITE}/jtreg/native
TEST_JDK=${JDK_LOCATION}/build/linux-x86_64-normal-server-release/images/jdk

NUM_CPUS=`grep -c ^processor /proc/cpuinfo`
CONCURRENCY=`expr $NUM_CPUS / 2`
MAX_RAM_PERCENTAGE=`expr 25 / $CONCURRENCY`

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

chmod +x ${JT_HOME}/bin/jtreg

if [ "${TEST_SUITE}" == "hotspot" ]; then
    ${JT_HOME}/bin/jtreg -dir:${JDK_LOCATION}/test/${TEST_SUITE}/jtreg -verbose:summary -nativepath:${TEST_NATIVE_LIB} -exclude:${JDK_LOCATION}/test/${TEST_SUITE}/jtreg/ProblemList.txt -conc:${CONCURRENCY} -vmoption:-XX:MaxRAMPercentage=${MAX_RAM_PERCENTAGE} -a -ignore:quiet -timeoutFactor:5 -agentvm -javaoption:-Djava.awt.headless=true "-k:(!ignore)&(!stress)" -testjdk:${TEST_JDK} ${TEST_GROUPS}
fi

if [ "${TEST_SUITE}" == "jdk" ]; then
    ${JT_HOME}/bin/jtreg -dir:${JDK_LOCATION}/test/${TEST_SUITE} -verbose:summary -nativepath:${TEST_NATIVE_LIB} -exclude:${JDK_LOCATION}/test/${TEST_SUITE}/ProblemList.txt -exclude:${SCRIPT_DIR}/exclude/ProblemList_jdk.txt -conc:1 -vmoption:-XX:MaxRAMPercentage=${MAX_RAM_PERCENTAGE} -a -ignore:quiet -timeoutFactor:5 -javaoption:-Djava.awt.headless=true "-k:(!headful)&(!printer)" -testjdk:${TEST_JDK} ${TEST_GROUPS}
fi

if [ "${TEST_SUITE}" == "langtools" ]; then
    ${JT_HOME}/bin/jtreg -dir:${JDK_LOCATION}/test/${TEST_SUITE} -verbose:summary -exclude:${JDK_LOCATION}/test/${TEST_SUITE}/ProblemList.txt -conc:${CONCURRENCY} -vmoption:-XX:MaxRAMPercentage=${MAX_RAM_PERCENTAGE} -a -ignore:quiet -timeoutFactor:5 -agentvm -testjdk:${TEST_JDK} ${TEST_GROUPS}
fi
