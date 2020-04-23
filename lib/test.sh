#!/bin/bash
set -ex

#read VERSION <<< $(python3.8 get_tag_version_component.py -t sapmachine-11.0.6+4-2-alpine)
VERSION=$(python3.8 get_tag_version_component.py -t sapmachine-11.0.6+4-2-alpine)
echo ${VERSION}
echo doof
exit

#_CONFIGURE_OPTS=$(python3.8 get_configure_opts.py)
#eval _CONFIGURE_ARR=($_CONFIGURE_OPTS)
eval _CONFIGURE_ARR=($(python3.8 get_configure_opts.py))

echo ${_CONFIGURE_ARR[4]}
#exit
#_CONFIGURE_OPTS=(--hans --diter "--with-vendor-name=SAP SE" --klaus)
#echo "${_CONFIGURE_OPTS[5]}"
#exit

bash ./unsinn \
--with-boot-jdk=$BOOT_JDK \
"${_CONFIGURE_ARR[@]}" \
--with-freetype=bundled
