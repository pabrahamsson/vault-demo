## Vault Demo

1. `oc new-app openshift/python~https://github.com/pabrahamsson/vault-demo`
2. `oc patch dc/vault-demo -p '{"spec":{"template":{"spec":{"serviceAccount":"<vault service account>"}}}}' --type=merge`
