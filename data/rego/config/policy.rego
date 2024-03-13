package validate

import future.keywords.in

istioCm = input.istioconfigmap

tempoCm = input.tempoconfigmap

# Check istio configmap has "tempo" as the tracing backend and tempo configmap is configured to recieve traces from istio
validate {
    # Check existance of the configmaps
	istioCm.kind == "ConfigMap"
	tempoCm.kind == "ConfigMap"

	# Check that the mesh config contains the substring "enableTracing: true"
	# This would be better to parse the data for actual tracing field - e.g., mesh.defaultConfig.tracing.zipkin.address - TBD
	contains(istioCm.data.mesh, "enableTracing: true")

	# Check that the mesh config contains the substring "tempo-tempo.tempo.svc:9411" -> Address of the zipkin service
	# This could also be any other kind of tracing backend that Istio supports, this particular implementation uses Zipkin
	contains(istioCm.data.mesh, "tempo-tempo.tempo.svc:9411")

	# Check that the tempo endpoint for zipkin matches the port from the service
	# This is another imperfect one, the tempo config is tempo.yaml and the zipkin endpoint is distributer.receivers.zipkin.endpoint...
	contains(tempoCm.data["tempo.yaml"], "endpoint: 0.0.0.0:9411")
    
	# The proxy.istio.io/config annotation on a pod overrides the mesh settings - check if this overrides anything?
	# Tracing typically doesn't grab every event, it looks like the config is to grab 100%.. should this be checked for compliance to this control as well?
}
