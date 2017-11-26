#! /usr/bin/env groovy
// pulls in HashiCorp vault env variables from environment
//  - VAULT_ADDR: address of Vault server
//  - VAULT_CACERT: CA cert that signed TLS cert on Vault server
//  if those are not set, fall back to in-cluster defaults


def getVaultAddr() {
    // in-cluster default vault server address; can be overridden below
    def vault_address = 'https://http.vault.svc.cluster.local:8200'
    def environment_configured_vault_addr = env.VAULT_ADDR
    if(environment_configured_vault_addr?.trim()) {
        vault_address = environment_configured_vault_addr
    }
    return vault_address
}

def getVaultCacert() {
    // in-cluster default vault ca certificate; can be overridden below
    def vault_cacertificate = '/var/run/secrets/kubernetes.io/serviceaccount/ca.crt'
    def environment_configured_vault_cacert = env.VAULT_CACERT
    if(environment_configured_vault_cacert?.trim()) {
        vault_cacertificate = environment_configured_vault_cacert
    }
    return vault_cacertificate
}

def getVaultToken() {
    withCredentials([[$class: 'UsernamePasswordMultiBinding',
                      credentialsId: 'vault',
                      usernameVariable: 'VAULT_USER',
                      passwordVariable: 'VAULT_PASSWORD']]) {
        def vault_addr = getVaultAddr()
        def vault_cacert = getVaultCacert()
        def token_auth_cmd = ['sh', '-c', "PATH=/usr/bin VAULT_ADDR=${vault_addr} VAULT_CACERT=${vault_cacert} /usr/local/bin/vault auth -method=ldap username=$VAULT_USER password=$VAULT_PASSWORD"]
        println("Attempting auth with command: " + token_auth_cmd)
        sout = token_auth_cmd.execute().text
        auth_token = sout.split("\n")[3].split(" ")[1].toString()
        return auth_token
    }
}
 
def getClusterTargets() {
// gets provisioner targets from Vault 
// returns a list used for dynamic Jenkinsfile parameters
    targets_list_cmd = 'landscape cluster list --git-branch='+env.BRANCH_NAME
    println("Running command: " + targets_list_cmd)
    sout = executeOrReportErrors(targets_list_cmd)
    // prepend targets with null value, which is default
    clusterTargets = sout.toString().split()
    if(clusterTargets.size() == 0) {
        error("No targets found in Vault (zero results returned from command)")
    }
    //return clusterTargets
    return ["minikube"]
}

def getCloudTargets() {
// gets provisioner targets from Vault 
// returns a list used for dynamic Jenkinsfile parameters
    targets_list_cmd = 'landscape cloud list --git-branch='+env.BRANCH_NAME
    println("Running command: " + targets_list_cmd)
    sout = executeOrReportErrors(targets_list_cmd)
    // prepend targets with null value, which is default
    targetsString = "\n" + sout.toString()
    if(targetsString.length() == 0) {
        error("No targets found in Vault (zero results returned from command)")
    }
    println("command output: " + targetsString)
    return targetsString
}

def getCloudForCluster(cluster_name) {
// returns a string containing a cloud id for a given cluster
    cloud_id_cmd = 'landscape cloud list --cluster='+cluster_name
    println("Running command: " + cloud_id_cmd)
    sout = executeOrReportErrors(cloud_id_cmd)
    // prepend targets with null value, which is default
    cloud_id = sout.toString().trim()
    if(cloud_id.length() == 0) {
        error("Cloud ID Not found for cluster name: "+cluster_name)
    }
    println("command output: " + cloud_id)
    return cloud_id
}

def executeOrReportErrors(command_string, working_dir='__none__') {
// executes a command, printing stderr if command fails
// returns command stdout string
    if(working_dir == '__none__') {
        working_dir = System.getProperty("user.dir")
    }
    println("using working_dir:" + working_dir)
    println("currentBuild:" + currentBuild)
    def vaultVars = []
    vaultVars.add('VAULT_ADDR=' +  getVaultAddr())
    vaultVars.add('VAULT_CACERT=' + getVaultCacert())
    vaultVars.add('VAULT_TOKEN=' + getVaultToken())

    def cmd_stdout = new StringBuilder(), cmd_stderr = new StringBuilder()
    def cmd_exe = command_string.execute(vaultVars, new File(working_dir))
    cmd_exe.consumeProcessOutput(cmd_stdout, cmd_stderr)
    cmd_exe.waitForOrKill(5000)
    if(cmd_exe.exitValue() != 0) {
        println("stdout: " + cmd_stdout)
        println("stderr: " + cmd_stderr)
        error("Command returned non-zero return value")
    }
    return cmd_stdout
}

def convergeCloud(cloud_name, dry_run=true) {
    if(cloud_name != "minikube") {
        def cmd = "landscape cloud converge --cloud=" + cloud_name

        if(dry_run) {
            cmd += " --dry-run"
        }
        println("Running command: " + cmd)
        sout = executeOrReportErrors(cmd)
        println(sout)
    } else {
        println("Skipping minikube cloud setup inside of Jenkins")
    }
}

def convergeCluster(cluster_name, dry_run=true) {
    if(cluster_name != "minikube") {
        def cmd = 'landscape cluster converge --cluster=' + cluster_name

        if(dry_run) {
            cmd += " --dry-run"
        }
        println("Running command: " + cmd)
        sout = executeOrReportErrors(cmd)
        println(sout)
    } else {
        println("Skipping minikube cluster setup inside of Jenkins")
    }
}

def convergeCharts(cluster_name, dry_run=true) {
    def cmd = 'landscape charts converge --git-branch='+env.BRANCH_NAME+' --cluster=' + cluster_name
    if(dry_run) {
        cmd += " --dry-run"
    }
    println("Running command: " + cmd)
    sout = executeOrReportErrors(cmd)
    println(sout)
}


properties([parameters([choice(choices: getClusterTargets().join('\n'), description: 'Kubernetes Context (defined in Vault)', name: 'CONTEXT', defaultValue: '')])])


node('landscape') {
    stage('Checkout') {
        def kubernetes_context = env.CONTEXT
        if (kubernetes_context != null && !kubernetes_context.isEmpty()) {
            print("Using Kubernetes context: " + kubernetes_context)
            checkout scm
        } else {
            error("CONTEXT not set (normal on first-run)")
        }
    }
    getClusterTargets().each { clusterName ->
        println("clusterName="+clusterName)
        def cloudName = getCloudForCluster(clusterName)
        println("cloudName="+cloudName)
        stage('Test Cloud ' + cloudName) {
            withEnv(['VAULT_ADDR='+getVaultAddr(),'VAULT_CACERT='+getVaultCacert(),'VAULT_TOKEN='+getVaultToken()]) {
                convergeCloud(cloudName, true)
            }
        }
        stage('Test Cluster ' + clusterName) {
            withEnv(['VAULT_ADDR='+getVaultAddr(),'VAULT_CACERT='+getVaultCacert(),'VAULT_TOKEN='+getVaultToken()]) {
                convergeCluster(clusterName, true)
            }
        }
        stage('Test Charts ' + clusterName) {
            withEnv(['VAULT_ADDR='+getVaultAddr(),'VAULT_CACERT='+getVaultCacert(),'VAULT_TOKEN='+getVaultToken()]) {
                convergeCharts(clusterName, true)
            }
        }
        stage('Converge Cloud ' + cloudName) {
            withEnv(['VAULT_ADDR='+getVaultAddr(),'VAULT_CACERT='+getVaultCacert(),'VAULT_TOKEN='+getVaultToken()]) {
                convergeCloud(cloudName, false)
            }
        }
        stage('Converge Cluster ' + clusterName) {
            withEnv(['VAULT_ADDR='+getVaultAddr(),'VAULT_CACERT='+getVaultCacert(),'VAULT_TOKEN='+getVaultToken()]) {
                convergeCluster(clusterName, false)
            }
        }
        stage('Converge Charts ' + clusterName) {
            withEnv(['VAULT_ADDR='+getVaultAddr(),'VAULT_CACERT='+getVaultCacert(),'VAULT_TOKEN='+getVaultToken()]) {
                convergeCharts(clusterName, false)
            }
        }
    }

}
