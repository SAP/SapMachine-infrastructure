#!/bin/bash

set -x

UNAME=`uname`

while getopts l:h:s:j: opt
do
   case $opt in
       l) JDK_LOCATION=$OPTARG;;
       h) JT_HOME=$OPTARG;;
       s) TEST_SUITE=$OPTARG;;
   esac
done

shift $((OPTIND-1))
TEST_GROUPS=$@

if [ -z "$JDK_LOCATION" ]; then
    echo "JDK Location not specified (-l)" >&2
    exit 1
fi

if [ -z "$JT_HOME" ]; then
    echo "JavaTest Home not specified (-h)" >&2
    exit 1
fi

if [ -z "$TEST_SUITE" ]; then
    echo "Test Suite not specified (-s)" >&2
    exit 1
fi

if [ -z "$TEST_GROUPS" ]; then
    echo "Test Groups not specified" >&2
    exit 1
fi

CURRENT_DIR=$PWD
cd ${JDK_LOCATION}/build

BUILD_TYPE="$(ls)"

cd $CURRENT_DIR

TEST_JDK=${JDK_LOCATION}/build/${BUILD_TYPE}/images/jdk
TEST_NATIVE_LIB=${JDK_LOCATION}/build/${BUILD_TYPE}/images/test/${TEST_SUITE}/jtreg/native

if [[ $UNAME == Darwin ]]; then
    NUM_CPUS=`sysctl -n hw.ncpu`
else
    NUM_CPUS=`grep -c ^processor /proc/cpuinfo`
fi

CONCURRENCY=`expr $NUM_CPUS / 2`
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

chmod +x ${JT_HOME}/bin/jtreg

export PATH=${TEST_JDK}:$PATH
export JT_JAVA=${TEST_JDK}
export JAVA_HOME=${TEST_JDK}

mkdir test_report_${TEST_SUITE}

# Use full concurrency and agentvm to let the tests pass as fast as possible.
if [ "${TEST_SUITE}" == "hotspot" ]; then
    ${JT_HOME}/bin/jtreg -dir:${JDK_LOCATION}/test/${TEST_SUITE}/jtreg -xml -verbose:summary -nativepath:${TEST_NATIVE_LIB} \
     -exclude:${JDK_LOCATION}/test/${TEST_SUITE}/jtreg/ProblemList.txt -exclude:${JDK_LOCATION}/test/${TEST_SUITE}/jtreg/ProblemList-SapMachine.txt \
     -conc:${NUM_CPUS} -vmoption:-Xmx384m -w:test_report_${TEST_SUITE}\JTWork -r:test_report_${TEST_SUITE}\JTreport \
     -a -ignore:quiet -timeoutFactor:5 -agentvm -javaoption:-Djava.awt.headless=true -javaoption:-DSCIMARK_2_CP=${SCIMARK_2_CP} "-k:(!ignore)&(!stress)&(!headful)" -testjdk:${TEST_JDK} ${TEST_GROUPS}
fi

if [ "${TEST_SUITE}" == "jdk" ]; then
    ${JT_HOME}/bin/jtreg -dir:${JDK_LOCATION}/test/${TEST_SUITE} -xml -verbose:summary -nativepath:${TEST_NATIVE_LIB} \
    -exclude:${JDK_LOCATION}/test/${TEST_SUITE}/ProblemList.txt -exclude:${JDK_LOCATION}/test/${TEST_SUITE}/ProblemList-SapMachine.txt  \
    -conc:${NUM_CPUS} -vmoption:-Xmx384m -w:test_report_${TEST_SUITE}\JTWork -r:test_report_${TEST_SUITE}\JTreport \
    -a -ignore:quiet -timeoutFactor:5 -agentvm -javaoption:-Djava.awt.headless=true "-k:(!headful)&(!printer)" -testjdk:${TEST_JDK} ${TEST_GROUPS}
fi

# Only use half number of CPUs because http://openjdk.java.net/jtreg/concurrency.html states the concurrency should be half the number of available CPUs.
if [ "${TEST_SUITE}" == "langtools" ]; then
    ${JT_HOME}/bin/jtreg -dir:${JDK_LOCATION}/test/${TEST_SUITE} -xml -verbose:summary \
    -exclude:${JDK_LOCATION}/test/${TEST_SUITE}/ProblemList.txt -exclude:${JDK_LOCATION}/test/${TEST_SUITE}/ProblemList-SapMachine.txt \
    -conc:${CONCURRENCY} -vmoption:-Xmx640m -w:test_report_${TEST_SUITE}\JTWork -r:test_report_${TEST_SUITE}\JTreport \
    -a -ignore:quiet -timeoutFactor:5 -agentvm -testjdk:${TEST_JDK} ${TEST_GROUPS}
fi
