# Principles
- Single point of control (branches of this repo) as Kubernetes deployments.
- Prevent configuration sprawl by supplying "building blocks" (Helm Charts)

## Why use Helm?
Helm is [an official Kubernetes](https://github.com/kubernetes/helm) package manager

Its strength is reusing and retooling config files
It promotes separation of concerns (secrets are external from Helm configs)

# Rapid iteration of Chart development
preferred method is CI system (Jenkins), for version-control/GitHub approval
this works great for local development of Charts
```
git clone https://github.com/shaneramey/helm-charts
cd helm-charts
helm upgrade nginx --namespace=jenkins nginx # near-instantaneous
```

# More about Helm

Helm claims to be "the best way to find, share, and use software built for Kubernetes".
A quote from the Helm README:
> Use Helm to...
> Find and use popular software packaged as Kubernetes charts
> Share your own applications as Kubernetes charts
> Create reproducible builds of your Kubernetes applications
> Intelligently manage your Kubernetes manifest files
> Manage releases of Helm packages

It has a vibrant developer community and a highly-active Slack channel

[Here is a repo of Landscape-compatible Helm Charts](https://github.com/shaneramey/helm-charts)

## Why use Landscape?
Landscape is currently the easiest way to define and enforce all Helm charts in a Kubernetes cluster.
It provides a single point of control (branches of this repo) as Kubernetes deployments.
Landscape implements the Features listed above painlessly.

The Landscape project itself currently has a much smaller fan-base than Helm.
This may be because it was only recently introduced, and is gaining traction.
Some or all of its functionality may be pulled into Helm eventually.

It handles deletes of objects by wiping out everything in the namespace that's not defined in Landscape.

