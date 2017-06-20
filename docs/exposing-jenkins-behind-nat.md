# Set up local GitHub automatic pushes


## Exposing jenkins to the Internet via a proxy service
Requirements: backplane.io free account
WARNING: This exposes your Jenkins server to the Internet, so make sure it is secured to only their IPs
[GitHub IPS](https://help.github.com/articles/github-s-ip-addresses/) should be updated regularly

backplane connect "endpoint=amicable-mouse-4.backplaneapp.io,release=v1" https://http.jenkins.svc.master.local
```
cat << EOF > iprules.txt
 allow 192.30.252.0/22
 allow 185.199.108.0/22
 deny all
EOF

backplane secure ip amicable-mouse-4.backplaneapp.io < iprules.txt

Follow instructions at http://www.inanzzz.com/index.php/post/ljgv/setup-github-and-jenkins-integration-for-pull-request-builder-and-merger to set up Jenkins and GitHub

## Jenkins setup
Manage Jenkins -> Configure System

Under "GitHub" section, do the following.

Click "Advanced" button.

Tick "Specify another hook url for GitHub configuration" tickbox and obtain URL https://amicable-mouse-4.backplaneapp.io/github-webhook/ somewhere then untick it again.

Exit without saving.

# GitHub setup
add Issue comment, Pull request and Push
