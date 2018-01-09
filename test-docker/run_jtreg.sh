#!/bin/bash

set -x

JDK_LOCATION=$1
TEST_JDK=$2
JT_HOME=$3
TEST_SUITE=$4
TEST_GROUPS=$5

TEST_NATIVE_LIB=${JDK_LOCATION}/build/linux-x86_64-normal-server-release/images/test/${TEST_SUITE}/jtreg/native

NUM_CPUS=`grep -c ^processor /proc/cpuinfo`
CONCURRENCY=`expr $NUM_CPUS / 2`
MAX_RAM_PERCENTAGE=`expr 25 / $CONCURRENCY`

chmod +x ${JT_HOME}/bin/jtreg

if [ "${TEST_SUITE}" == "hotspot" ]; then
    ${JT_HOME}/bin/jtreg -dir:${JDK_LOCATION}/test/${TEST_SUITE}/jtreg -verbose:summary \
    -nativepath:${TEST_NATIVE_LIB} -exclude:${JDK_LOCATION}/test/${TEST_SUITE}/jtreg/ProblemList.txt \
    -conc:${CONCURRENCY} -vmoption:-XX:MaxRAMPercentage=${MAX_RAM_PERCENTAGE} \
    -a -ignore:quiet -timeoutFactor:5 -agentvm -javaoption:-Djava.awt.headless=true "-k:(!ignore)&(!stress)" \
    -testjdk:${TEST_JDK} ${TEST_GROUPS}
fi

if [ "${TEST_SUITE}" == "jdk" ]; then
    ${JT_HOME}/bin/jtreg -dir:${JDK_LOCATION}/test/${TEST_SUITE} -verbose:summary \
    -nativepath:${TEST_NATIVE_LIB} -exclude:${JDK_LOCATION}/test/${TEST_SUITE}/ProblemList.txt \
    -conc:${CONCURRENCY} -vmoption:-XX:MaxRAMPercentage=${MAX_RAM_PERCENTAGE} \
    -a -ignore:quiet -timeoutFactor:5 -agentvm -javaoption:-Djava.awt.headless=true "-k:(!headful)&(!printer)" \
    -testjdk:${TEST_JDK} ${TEST_GROUPS}
fi

if [ "${TEST_SUITE}" == "langtools" ]; then
    ${JT_HOME}/bin/jtreg -dir:${JDK_LOCATION}/test/${TEST_SUITE} -verbose:summary \
    -exclude:${JDK_LOCATION}/test/${TEST_SUITE}/ProblemList.txt -conc:${CONCURRENCY} \
    -vmoption:-XX:MaxRAMPercentage=${MAX_RAM_PERCENTAGE} -a -ignore:quiet -timeoutFactor:5 -agentvm \
    -testjdk:${TEST_JDK} ${TEST_GROUPS}
fi
