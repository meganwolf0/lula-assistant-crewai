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
