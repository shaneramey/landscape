#! /bin/sh

GIT_BRANCH=`git symbolic-ref HEAD 2>/dev/null | cut -d"/" -f 3`

dig +short kubernetes.default.svc.${GIT_BRANCH}.local @10.0.0.10
if [ $? -ne 0 ]; then
    echo "failure in kubedns service test. Exiting"
    exit 1
else
    echo DNS Verify Passed!
fi

# Test all helm releases
for release in `helm list -q`; do
    helm test $release
done
