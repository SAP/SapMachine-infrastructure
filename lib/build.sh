#!/bin/bash
#set -ex
set -e

if [[ -z $WORKSPACE ]]; then
  WORKSPACE=$PWD
fi

UNAME=`uname`
if [[ $UNAME == Darwin ]]; then
    SEDFLAGS='-En'
else
    SEDFLAGS='-rn'
fi

if [[ $UNAME == CYGWIN* ]]; then
  WORKSPACE=$(cygpath -u "${WORKSPACE}")
fi

GTEST_DIR="${WORKSPACE}/gtest"
export GTEST_DIR

cd "${WORKSPACE}/SapMachine"

echo "Git Revision=$(git rev-parse HEAD)"

if [ -z $BOOT_JDK ]; then
  # error
  echo "No boot JDK specified!"
  exit 1
fi

# use a devkit, if set
if [ ! -z $DEVKIT_PATH ]; then
  if [[ $UNAME == Darwin ]]; then
    _DEVKIT_OPTION="--with-xcode-path=$DEVKIT_PATH"
  else
    _DEVKIT_OPTION="--with-devkit=$DEVKIT_PATH"
  fi
fi

if [[ $UNAME == Darwin ]]; then
  _CONFIGURE_OS_OPTIONS="--with-macosx-bundle-name-base=SapMachine --with-macosx-bundle-id-base=com.sap.openjdk"
fi

if [[ $UNAME == CYGWIN* ]]; then
  _CONFIGURE_OS_OPTIONS="--with-jdk-rc-name=SapMachine --with-external-symbols-in-bundles=public"
fi

if [[ ! -z $SAPMACHINE_VERSION ]]; then
  _GIT_TAG=" -t $SAPMACHINE_VERSION"
fi
if [[ ! -z $JDK_BUILD ]]; then
  _JDK_BUILD=" -b $JDK_BUILD"
fi

echo "PATH before configure and make: ${PATH}"

# need to do the python call first and the eval in a second step to bail out on $? != 0
_CONFIGURE_OPTS=$(python3 ../SapMachine-infrastructure/lib/get_configure_opts.py $_GIT_TAG $_JDK_BUILD)
eval _CONFIGURE_OPTS=(${_CONFIGURE_OPTS})

# test/trace call to codesign to have some indication of potential problems
if [[ $UNAME == Darwin ]] && [[ $RELEASE_BUILD == true]]; then
  echo "Testing codesign call..."
  touch cstest
  codesign -s "Developer ID Application: SAP SE (7R5ZEU67FQ)" cstest || echo codesignerror=true
  rm cstest
  if [[ $codesignerror ]]; then
    echo "Failed."
    exit 1
  fi
fi

(set -x && bash ./configure \
--with-boot-jdk=$BOOT_JDK \
"${_CONFIGURE_OPTS[@]}" \
$_DEVKIT_OPTION \
$_CONFIGURE_OS_OPTIONS \
--disable-dtrace \
--with-freetype=bundled \
$EXTRA_CONFIGURE_OPTIONS)

(set -x && make JOBS=12 product-bundles legacy-bundles test-image)
