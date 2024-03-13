package validate

import future.keywords.every
import future.keywords.in

# Tracing is implemented via istio-proxy sidecar containers. Check that all workloads have the sidecar injected.
# This function has been used before, good to identify how we can pull this out and reuse it.

validate {
	every pod in input.pods {
		pod.kind == "Pod"
		allowed_pod(pod)
	}
}

allowed_pod(pod) {
	images := pod.spec.containers[_].image
	contains(images, "proxyv2")
}

allowed_pod(pod) {
	exempt := {"kube-system", "istio-system", "istio-operator", "flux-system", "kyverno"} # to pass on metallb k3d, add: "metallb-system"
	pod.metadata.namespace in exempt
}
