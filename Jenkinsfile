#! /usr/bin/env groovy
// pulls in HashiCorp vault env variables from environment
//  - VAULT_ADDR: address of Vault server
//  - VAULT_CACERT: CA cert that signed TLS cert on Vault server
//  if those are not set, fall back to in-cluster defaults

@Library('vaultHelpers') _

def getK8sClusterTargets() {
    println(env.getEnvironment())

    // Optional filter
    def branch_selector_for_clusters = env.BRANCH_NAME

    // Vault connection parameters
    def vault_addr = vaultHelpers.getVaultAddr()
    def vault_cacert = vaultHelpers.getVaultCacert()
    def vault_token = vaultHelpers.getVaultToken()

    // Read Projects from Vault
    def clusters = [
      'sh',
      '-c',
      "PATH=/usr/local/bin VAULT_ADDR=${vault_addr} " + \
      "VAULT_CACERT=${vault_cacert} " + \
      "VAULT_TOKEN=${vault_token} " + \
      "landscape cluster list --git-branch=${branch_selector_for_clusters}"
    ]

    println("Getting K8S clusters for branch " + branch_selector_for_clusters)
    sout = clusters.execute().text.split("\n")
    return sout
}

// Generate target list of GCP Projects
def allK8sClusters = getK8sClusterTargets()

// Create job per-target under this folder
def jenkinsJobFolder = 'k8s-clusters'

// properties([parameters([choice(choices: getClusterTargets().join('\n'), description: 'Kubernetes Context (defined in Vault)', name: 'CONTEXT', defaultValue: '')])])

properties([
  parameters([
    choice(choices: "(all)\n" + allK8sClusters.join('\n'),
               description: 'Kubernetes Cluster',
               name: 'K8S_CLUSTER',
           defaultValue: '(all)'
    )
  ])
])
println(env.getEnvironment())

node('landscape') {
  def seed_job_url = scm.getUserRemoteConfigs()[0].getUrl()

  // create a GCP-specific Jenkins job for each listed in Vault
  allK8sClusters.each {
    jobDsl scriptText: """folder("${jenkinsJobFolder}")
    pipelineJob("${jenkinsJobFolder}" + "/" + "${it}") {
      definition {
        cps {
          script(\"\"\"
            @Library('vaultHelpers') _

            properties(
                [
                    pipelineTriggers([cron('*/3 * * * *')]),
                ]
            )
            def setupKubectlCredentials(cluster_name, dry_run=true) {
                def cmd = 'landscape cluster converge --cluster=' + cluster_name
                if(dry_run) {
                    cmd += " --dry-run"
                }
                println("Running command: " + cmd)
                sh cmd
            }

            def convergeCharts(cluster_name, dry_run=true) {
                def cmd = 'landscape charts converge --cluster=' + cluster_name
                if(dry_run) {
                    cmd += " --dry-run"
                }
                println("Running command: " + cmd)
                sh cmd
            }

            node {
              // clone branch of seed job
              git url: "${seed_job_url}",
                  branch: 'master',
                  credentialsId: 'github'

              // credentials is of kind 'Secret file', downloaded from GCP SA
              withCredentials([
                file(credentialsId: 'gcp-staging',
                     variable: 'GOOGLE_APPLICATION_CREDENTIALS')
              ]) {
                withEnv(['VAULT_ADDR='+vaultHelpers.getVaultAddr(),
                         'VAULT_CACERT='+vaultHelpers.getVaultCacert(),
                         'VAULT_TOKEN='+vaultHelpers.getVaultToken()]) {

                    stage('Environment') {
                        setupKubectlCredentials("${it}", false)
                        sh 'helm repo add chartmuseum http://http.chartmuseum.svc.cluster.local:8080'
                    }

                    stage('Test Charts ' + "${it}") {
                        convergeCharts("${it}", true)
                    }

                    stage('Converge Charts ' + "${it}") {
                        convergeCharts("${it}", false)
                    }
                }
              }
            }
          \"\"\".stripIndent())
        }
      }
    }"""
  }
}

stage("Applying Helm Charts to Kubernetes Cluster(s)") {
    def builds = [:]

    for (k8sCluster in allK8sClusters) {
        def jobName = jenkinsJobFolder + '/' + k8sCluster
        builds["${k8sCluster}"] = {
            node('landscape') {
                build job: jobName
            }
        }
    }
    parallel builds
}
