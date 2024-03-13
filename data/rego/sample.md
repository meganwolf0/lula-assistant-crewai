# Sample Rego Policies

The following policies, and linked data input files, are fed into Open Policy Agent to provide evidence as to how the tool Tempo, running in a Big Bang Kubernetes cluster, meets some FedRAMP High control requirements.

## Perform healthcheck for Tempo
### Input
[Input file](./healthcheck/data.json)

### Rego Policy
```
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
```

## Check audit log storage capacity
### Input
[Input file](./audit-log-capacity/data.json)

### Rego Policy
```
package validate

import future.keywords.every
import future.keywords.in

# Validate that the audit log storage capacity is sufficient to accommodate organization-defined audit log retention requirements.
# For each storage class used in the pvc, check "allowVolumeExpansion: true" -> This is a property of the storage class
validate {
	every pvc in input.persistentvolumeclaims {
		pvc.kind == "PersistentVolumeClaim"
		storageClassName := pvc.spec.storageClassName

		storageClass := findStorageClassByName(input.storageclasses, storageClassName)
		storageClassValid(storageClass)
	}
}

findStorageClassByName(sc, name) := i {
	i := sc[_]
	i.metadata.name == name
}

storageClassValid(sc) {
	sc.allowVolumeExpansion == true
}
```

## Check Tempo UI available
### Input
[Input file](./ui-available/data.json)

### Rego Policy
```
package validate

import future.keywords.every

tempoSvc = input.temposvc
tempoVs = input.tempovs

validate {
    # Existance of tempoSvc and tempoVs
    tempoSvc.kind == "Service"
    tempoVs.kind == "VirtualService"

	# The virtual service should route to the tempo service
	destinationPorts := [port | route := tempoVs.spec.http[_].route[_]; destination := route.destination; port := destination.port.number]
	every port in destinationPorts {
		service_provided_port(port)
	}
}

service_provided_port(vsPort) {
	# Check that some port is broadcasting on the expected virtual service port
	port := tempoSvc.spec.ports[_]
	port.targetPort == vsPort
}

```

## Check tempo configuration
### Input
[Input file](./config/data.json)

### Rego Policy
```
package validate

# Check istio configmap has "tempo" as the tracing backend and tempo configmap is configured to recieve traces from istio
validate {
# Check that the istio config contains the setting "enableTracing: true"
    input.istioconfig.enableTracing == true

# Check that the mesh config contains the substring "tempo-tempo.tempo.svc:9411" -> Address of the zipkin service
    input.istioconfig.defaultConfig.tracing.zipkin.address == "tempo-tempo.tempo.svc:9411"

# Check that the tempo is broadcasting data on the right port
    input.tempoconfig.distributor.receivers.zipkin.endpoint == "0.0.0.0:9411"
    
# The proxy.istio.io/config annotation on a pod overrides the mesh settings - check if this overrides anything?
# Tracing typically doesn't grab every event, it looks like the config is to grab 100%.. should this be checked for compliance to this control as well?
}
```
