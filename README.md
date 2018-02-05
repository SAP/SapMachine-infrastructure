# SapMachine Build Infrastructure

## Description

This repository contains the script files and Jenkins pipeline definitions, that we use to automate repository 
updates and builds of https://github.com/SAP/SapMachine. 
The jobs run on our Jenkins installation https://sapmachine-ci.sapcloud.io/.


### Jenkis Configuration
* Build-jobs run in docker containers to have a reproducible build envrironment.
* Different build-jobs use the same Pipeline with different parameters.
* Build jobs start test jobs. However, we don't use the result of the tests as indicator of a failure of the build job, as some failures have to be considered a *normal*. Some tests are shaky, others are open issues that will be fixed with the new build. However, we should compare our results to the results reported here: http://download.java.net/openjdk/testresults/10/testresults.html

### Branches in the SapMachine Repository

The SapMachine Github Repository https://github.com/SAP/SapMachine is oranized into the following branches.

* Mercurial repos are imported to branches **jdk/jdk** and **jdk/jdk10**.
* We look every view hours into the upstream mercurial repositories and add new changes and tags.
    * On jenkins: *update-pipeline* https://sapmachine-ci.sapcloud.io/view/repository-update/job/update-pipeline/.
* **sapmachine10**: **jdk/jdk10** + our changes.
    * **sapmachine**: **jdk/jdk** + our changes.
    * **sapmachine10-alpine**: **sapmachine10** + alpine changes.
    * **sapmachine-alpine**: **sapmachine** + alpine changes.
* We cherry-pick our changes between sapmachine and sapmachine10
* We merge **jdk/jdk10** and **jdk/jdk** with new build tags.
* Jenkins look for new tags, open pull request and validate.
    * Check for new tags: *check-tag-pipeline* 
    * Triggered by *update-pipeline*
    * Merge is triggered manually (Push the button on github).


