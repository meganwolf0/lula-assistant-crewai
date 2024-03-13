package validate

import future.keywords.every
import future.keywords.in

# Readiness check on tempo pods
validate {
	every statefulset in input.statefulsets {
		statefulset.kind == "StatefulSet"
		podsRequired := statefulset.status.replicas
		podsReady := statefulset.status.readyReplicas
		podsReady == podsRequired
	}
}
