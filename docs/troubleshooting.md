### Troubleshooting
If values aren't updating with a script like:
```
kubectl delete secret helm-chart-publisher-helm-chart-publisher ; make -C ../apps/helm-chart-publisher publish_helm && helm repo update && helm local_bump -f helm-chart-publisher/helm-chart-publisher/helm-chart-publisher.yaml --patch && make deploy

make -C ../helm-charts/ publish_helm && helm repo update && helm local_bump -f openvpn/openvpn/openvpn.yaml --patch && make deploy
```
Try:
```
helm delete helm-chart-publisher-helm-chart-publisher  --purge
```
