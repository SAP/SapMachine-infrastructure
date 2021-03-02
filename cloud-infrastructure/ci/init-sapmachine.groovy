/**
Copyright (c) 2001-2021 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
**/

@Grab('org.yaml:snakeyaml:1.17')

import jenkins.model.*
import jenkins.security.s2m.AdminWhitelistRule
import hudson.security.*
import hudson.util.Secret
import com.cloudbees.plugins.credentials.*
import com.cloudbees.plugins.credentials.common.*
import com.cloudbees.plugins.credentials.domains.*
import com.cloudbees.plugins.credentials.impl.*
import com.cloudbees.jenkins.plugins.sshcredentials.impl.*
import org.jenkinsci.plugins.plaincredentials.*
import org.jenkinsci.plugins.plaincredentials.impl.*
import org.yaml.snakeyaml.Yaml

jenkins_home = System.getenv("JENKINS_HOME")
jenkins_root_url = "https://${System.getenv("VIRTUAL_HOST")}/"
instance = Jenkins.getInstance()

void runCmd(String cmd) {
    def process = new ProcessBuilder(cmd.split(" ")).redirectErrorStream(true).start()
    process.inputStream.eachLine { println it }
}

int getInitLevel() {
    File initFile = new File("${jenkins_home}/sapmachineInitLevel")

    if (!initFile.exists()) {
        initFile.write("0")
    }

    def initLevel = initFile.text.toInteger()
    println "--> initLevel=${initLevel}"
    return initLevel
}

void updateInitLevel() {
    File initFile = new File("${jenkins_home}/sapmachineInitLevel")

    def level = initFile.text.toInteger()
    initFile.write(Integer.toString(level+1))
}

if (0 == getInitLevel()) {
    updateInitLevel()

    println "--> importing credentials"
    def domain = Domain.global()
    def store = instance.getExtensionList('com.cloudbees.plugins.credentials.SystemCredentialsProvider')[0].getStore()
    Yaml parser = new Yaml()
    def credentials = parser.load(("/var/clients/credentials.yml" as File).text)

    for (def secretText : credentials["secret_text"]) {
        def secretTextCred = new StringCredentialsImpl(
            CredentialsScope.GLOBAL,
            secretText["id"],
            secretText["description"],
            Secret.fromString(secretText["text"]))
        store.addCredentials(domain, secretTextCred)
    }

    for (def userPassword : credentials["user_password"]) {
        def userPasswordCred = new UsernamePasswordCredentialsImpl(
            CredentialsScope.GLOBAL,
            userPassword["id"],
            userPassword["description"],
            userPassword["user"],
            userPassword["password"])
        store.addCredentials(domain, userPasswordCred)
    }

    runCmd("rm -rf /var/clients/credentials.yml")
    println "--> importing credentials ... done"

    // enable server client security
    instance.getInjector().getInstance(AdminWhitelistRule.class).setMasterKillSwitch(false)

    Thread.start {
        sleep 10000
        println "--> applying Jenkins configuration"
        runCmd("git clone https://github.com/sap/SapMachine-infrastructure /tmp/SapMachine-infrastructure")
        runCmd("python3 /tmp/SapMachine-infrastructure/lib/jenkins_restore.py -s /tmp/SapMachine-infrastructure -t ${jenkins_home}")
        runCmd("rm -rf /tmp/SapMachine-infrastructure")
        println "--> applying Jenkins configuration ... done"

        // reload the configuration after it was written to disk
        instance.doReload()

        Thread.start {
            sleep 5000

            jlc = JenkinsLocationConfiguration.get()
            jlc.setUrl(jenkins_root_url)
            jlc.save()

            println "--> store client information"
            for (client in hudson.model.Hudson.instance.slaves) {
                File clientSecret = new File("/var/clients/${client.name}.txt")
                clientSecret.write("${client.getComputer().getJnlpMac()}")
            }
            println "--> store client information ... done"

            // restart the jenkins instance
            instance.restart()

            println "--> creating local user 'SapMachine'"
            File passwordFile = new File("${jenkins_home}/secrets/sapmachinePassword")
            String password = UUID.randomUUID().toString().replace("-", "")
            passwordFile.write("${password}\n")

            def hudsonRealm = new HudsonPrivateSecurityRealm(false)
            hudsonRealm.createAccount('SapMachine', password)
            instance.setSecurityRealm(hudsonRealm)

            def strategy = new FullControlOnceLoggedInAuthorizationStrategy()
            instance.setAuthorizationStrategy(strategy)
            instance.save()
            println "--> creating local user 'SapMachine' ... done"
        }
    }
}
