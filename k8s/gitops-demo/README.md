# GitOps Drift Demonstration

## Purpose

Demonstrate desired state versus actual state in Kubernetes and prepare
a dedicated application for GitOps management with Argo CD.

## Resource

`drift-demo.yaml` defines a Deployment named `gitops-drift-demo`
in the `microservices` namespace.

The desired state is:
- Replicas: 2
- Image: nginx:1.27
- Container port: 80
- CPU request: 10m; limit: 100m
- Memory request: 16Mi; limit: 64Mi

## Manual Drift Experiment

1. Apply the manifest:

   `kubectl apply -f k8s/gitops-demo/drift-demo.yaml`

2. Verify two replicas:

   `kubectl get deployment gitops-drift-demo -n microservices`

3. Create drift by scaling the Deployment to three replicas:

   `kubectl scale deployment gitops-drift-demo -n microservices --replicas=3`

4. Reconcile manually by applying the manifest again:

   `kubectl apply -f k8s/gitops-demo/drift-demo.yaml`

5. Verify that the Deployment returns to two replicas.

## GitOps Next Step

Configure Argo CD to monitor this dedicated directory in Git and
compare the repository's desired state with the live cluster state.
Automatic synchronization and self-healing will be tested separately.
