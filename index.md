---
layout: default
title: SapMachine
---

**SapMachine** is a distribution of the OpenJDK maintained by SAP. It is designed to be free, cross-platform, production-ready, and Java SE certified. This distribution serves as the default Java Runtime for SAP's numerous applications and services.

<img align="left" width="240" src="assets/images/logo_circular.svg" alt="SapMachine-Logo: the OpenJDK-distribution from SAP">

SapMachine supports all major operating systems.
It comes with long-term support releases that include bug fixes and performance updates.

Our goal is to keep SapMachine as close to OpenJDK as possible,
only adding additional features when absolutely necessary.

Our team's many contributions to the OpenJDK and the ecosystem include the PowerPC/AIX support, elastic Metaspace,
 helpful NullPointerExceptions, a website for JFR events and more.

## Download

In the following, you find downloads of SapMachine and our build of JDK Mission Control (JMC):

<select id="sapmachine_major_select" class="download_select" aria-label="Select the major version of the SapMachine you want to download">
</select>

<select id="sapmachine_imagetype_select" class="download_select" aria-label="Select either JDK or JRE of SapMachine you want to download">
</select>

<select id="sapmachine_os_select" class="download_select" aria-label="Select the target Operating System of the SapMachine you want to download">
</select>

<select id="sapmachine_version_select" class="download_select" aria-label="Select the version of SapMachine you want to download">
</select>

<button id="sapmachine_download_button" type="button" class="download_button" aria-label="Download SapMachine in the configured release, type, OS and version">Download</button>

<div class="download_label_section">
  <div id="download_label" class="download_label"></div>
  <button id="sapmachine_copy_button" type="button" class="download_button" aria-label="Copy the download URL of the SapMachine release configured by release, type, OS and version">Copy Download URL</button>
</div>

<div class="download_filter">
  <input type="checkbox" id="sapmachine_lts_checkbox" name="lts" aria-label="If checked, Long Term Support Releases (LTS) of SapMachine will be offered in the list for download (default)" checked>
  <label for="lts">Long Term Support Releases (LTS)</label>

  <input type="checkbox" id="sapmachine_nonlts_checkbox" name="nonlts" aria-label="If checked, Short Term Support Releases of SapMachine will be offered in the list for download (default)" checked>
  <label for="nonlts">Short Term Support Releases</label>

  <input type="checkbox" id="sapmachine_ea_checkbox" name="ea" aria-label="If checked, Pre-Releases of SapMachine will be offered in the list for download">
  <label for="ea">Pre-Releases</label>
</div>

## Documentation

Check out our [FAQs](https://github.com/SAP/SapMachine/wiki/Frequently-Asked-Questions) and [Documentation pages](https://github.com/SAP/SapMachine/wiki) for more information, including:

* [Installation Manual](https://github.com/SAP/SapMachine/wiki/Installation) and [Docker Images](https://github.com/SAP/SapMachine/wiki/Docker-Images)
* [Maintenance and Support of SapMachine](https://github.com/SAP/SapMachine/wiki/Maintenance-and-Support)
* [Certifications and Java Compatibility](https://github.com/SAP/SapMachine/wiki/Certification-and-Java-Compatibility)
* [List of Differences between SapMachine and OpenJDK](https://github.com/SAP/SapMachine/wiki/Differences-between-SapMachine-and-OpenJDK)
