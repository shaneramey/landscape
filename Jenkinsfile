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
    targetsString = "\n" + sout.toString()
    if(targetsString.length() == 0) {
        error("No targets found in Vault (zero results returned from command)")
    }
    println("command output: " + targetsString)
    return targetsString
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

def executeOrReportErrors(command_string, working_dir='/') {
// executes a command, printing stderr if command fails
// returns command stdout string
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
    def mkParams = "CLOUD_NAME=" + cloud_name
    if(dry_run) {
        mkParams += " DRYRUN=true"
    }
    def cmd = "make " + mkParams + " cloud"
}

def convergeCluster(cluster_name, dry_run=true) {
    def mkParams = "SKIP_CONVERGE_CLOUD=true CLUSTER_NAME=" + cluster_name
    if(dry_run) {
        mkParams += " DRYRUN=true"
    }
    def cmd = "make " + mkParams + " cluster"
}

def convergeCharts(cluster_name, dry_run=true) {
    def mkParams = "SKIP_CONVERGE_CLOUD=true SKIP_CONVERGE_CLUSTER=true " + \
                    "CLUSTER_NAME=" + cluster_name
    if(dry_run) {
        mkParams += " DRYRUN=true"
    }
    def cmd = "make " + mkParams + " charts"
}

def clusters_for_branch(branch_name) {
    clusters_list_cmd = 'landscape cluster list --git-branch='+branch_name
    println("Running command: " + clusters_list_cmd)
    sout = executeOrReportErrors(clusters_list_cmd)
    // prepend targets with null value, which is default
    targetsString = "\n" + sout.toString()
    if(targetsString.length() == 0) {
        error("No clusters found in Vault (zero results returned from command)")
    }
    println("command output: " + targetsString)
    return targetsString
}

properties([parameters([choice(choices: getClusterTargets(), description: 'Kubernetes Context (defined in Vault)', name: 'CONTEXT', defaultValue: '')])])


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
    for (String cluster_name : clusters_for_branch(${env.BRANCH_NAME})) {
        def cloud_name = getCloudForCluster(cluster_name)
        stage('Test Cloud ' + cloud_name) {
            withEnv(['VAULT_ADDR='+getVaultAddr(),'VAULT_CACERT='+getVaultCacert(),'VAULT_TOKEN='+getVaultToken()]) {
                convergeCloud(cloud_name, true)
            }
        }
        stage('Test Cluster ' + cluster_name) {
            withEnv(['VAULT_ADDR='+getVaultAddr(),'VAULT_CACERT='+getVaultCacert(),'VAULT_TOKEN='+getVaultToken()]) {
                convergeCluster(cluster_name, true)
            }
        }
        stage('Test Charts ' + cluster_name) {
            withEnv(['VAULT_ADDR='+getVaultAddr(),'VAULT_CACERT='+getVaultCacert(),'VAULT_TOKEN='+getVaultToken()]) {
                convergeCharts(cluster_name, true)
            }
        }
        stage('Converge Cloud ' + cloud_name) {
            withEnv(['VAULT_ADDR='+getVaultAddr(),'VAULT_CACERT='+getVaultCacert(),'VAULT_TOKEN='+getVaultToken()]) {
                convergeCloud(cloud_name, false)
            }
        }
        stage('Converge Cluster ' + cluster_name) {
            withEnv(['VAULT_ADDR='+getVaultAddr(),'VAULT_CACERT='+getVaultCacert(),'VAULT_TOKEN='+getVaultToken()]) {
                convergeCluster(cluster_name, false)
            }
        }
        stage('Converge Charts ' + cluster_name) {
            withEnv(['VAULT_ADDR='+getVaultAddr(),'VAULT_CACERT='+getVaultCacert(),'VAULT_TOKEN='+getVaultToken()]) {
                convergeCharts(cluster_name, false)
            }
        }
    }
}
