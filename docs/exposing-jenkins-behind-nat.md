# Set up local GitHub automatic pushes

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

