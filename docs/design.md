# Why use Landscaper/Helm

TODO: talk about pattern vs. anti pattern, stateless message queues, consistency vs  availability (when there is network partition), screenshot, statefulset leads towards consistency instead of availability - statefulset keeps identity, ThirdPartyResource. Simplicity of root environment build system

Instead of writing Chef cookbooks, we write Helm Charts. Everyone does.

By using established framework (Helm) we can focus on the interesting Kubernetes features:
- Blue/Green deployments

By using a desired-state config repo, we nip sprawling deployments in the bud

We can tune the edges and let community developers make improvements to the core.
