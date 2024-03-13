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
