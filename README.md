# Kubernetes Microservices Platform

A hands-on DevOps project demonstrating how to containerize, deploy, scale, and troubleshoot Python microservices using Docker, Kubernetes, and supporting cloud-native tools.

This project is being developed incrementally, with an emphasis on practical implementation, operational troubleshooting, reliability, and interview-ready understanding.

## Architecture

The platform contains two FastAPI microservices:

- **Product Service** — exposes product information through a REST API.
- **Order Service** — retrieves product information from Product Service to create a demonstration order.

The services can run locally using Docker Compose or inside a local Kubernetes cluster created with `kind`.

```text
                  Client
                    |
          +---------+---------+
          |                   |
          v                   v
   Product Service      Order Service
      FastAPI               FastAPI
          ^                   |
          |                   |
          +-------------------+
             HTTP request
          to Product Service

       Local Kubernetes (kind)
       Namespace: microservices
```

In Kubernetes, each application runs in a Deployment and is exposed internally through a ClusterIP Service. Kubernetes DNS allows Order Service to reach Product Service using its Service name.

## Technology Stack

- Python 3.12
- FastAPI and Uvicorn
- HTTPX for inter-service HTTP requests
- Docker and Docker Compose
- Kubernetes and `kubectl`
- `kind` — Kubernetes in Docker
- Kubernetes ConfigMaps and Secrets
- Readiness and liveness probes
- Resource requests and limits
- Horizontal Pod Autoscaler (HPA)
- NGINX Ingress
- Metrics Server

## Project Structure

```text
k8s-microservices-platform/
├── services/
│   ├── product-service/
│   │   ├── app/
│   │   │   └── main.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── order-service/
│       ├── app/
│       │   └── main.py
│       ├── Dockerfile
│       └── requirements.txt
├── k8s/
│   ├── product-service.yaml
│   ├── order-service.yaml
│   ├── order-service-config.yaml
│   ├── product-service-hpa.yaml
│   ├── product-ingress.yaml
│   ├── volume-demo.yaml
│   └── app-secret.yaml       # Local-only; ignored by Git
├── docker-compose.yml
├── .gitignore
└── README.md
```

## Services and API Endpoints

### Product Service

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/version` | Returns the service version |
| GET | `/products` | Lists available products |
| GET | `/products/{product_id}` | Retrieves a product by ID |

Sample product IDs: `1`, `2`, and `3`.

### Order Service

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/orders/demo` | Creates a demonstration order using Product Service data |

The Order Service uses the `PRODUCT_SERVICE_URL` environment variable to locate Product Service. Its HTTP request has a three-second timeout, and dependency failures are returned as HTTP 502 responses.

The demonstration order is not persisted to a database.

## Run Locally with Docker Compose

### Prerequisites

Install Docker and Docker Compose.

Build and start both services:

```bash
docker compose up --build -d
```

Check the running containers:

```bash
docker compose ps
```

Test the APIs:

```bash
curl http://localhost:8001/health
curl http://localhost:8001/products
curl http://localhost:8001/version

curl http://localhost:8002/health
curl http://localhost:8002/orders/demo
```

View service logs:

```bash
docker compose logs -f product-service
docker compose logs -f order-service
```

Stop the services:

```bash
docker compose down
```

Docker Compose configures Order Service to call Product Service using the internal service name `product-service`.

## Run in Kubernetes

The Kubernetes manifests target a local `kind` cluster and use the `microservices` namespace.

### 1. Verify the cluster

```bash
kubectl config current-context
kubectl get nodes
```

The expected context for this lab is `kind-microservices`.

If the cluster does not exist, create it:

```bash
kind create cluster --name microservices
```

### 2. Build the application images

Run these commands from the repository root:

```bash
docker build \
  -t k8s-microservices-platform-product-service:v2 \
  ./services/product-service

docker build \
  -t k8s-microservices-platform-order-service:latest \
  ./services/order-service
```

Load the images into the `kind` cluster:

```bash
kind load docker-image \
  k8s-microservices-platform-product-service:v2 \
  --name microservices

kind load docker-image \
  k8s-microservices-platform-order-service:latest \
  --name microservices
```

The local image tags must match the tags in the Kubernetes Deployment manifests.

### 3. Create the namespace and application configuration

```bash
kubectl create namespace microservices \
  --dry-run=client -o yaml | kubectl apply -f -
```

Apply the ConfigMap:

```bash
kubectl apply -f k8s/order-service-config.yaml
```

Create a dummy practice Secret for the current manifest:

```bash
kubectl create secret generic app-secret \
  --namespace microservices \
  --from-literal=DB_PASSWORD='local-practice-only' \
  --dry-run=client -o yaml | kubectl apply -f -
```

This value is for local practice only. The current application does not use this password, and no real credentials should be committed to Git.

### 4. Deploy the services

```bash
kubectl apply -f k8s/product-service.yaml
kubectl apply -f k8s/order-service.yaml
```

Wait for the Deployments to become ready:

```bash
kubectl rollout status deployment/product-service -n microservices
kubectl rollout status deployment/order-service -n microservices
```

Inspect the resources:

```bash
kubectl get deployments,pods,services -n microservices
kubectl get endpointslices -n microservices
```

### 5. Test the APIs

Use port forwarding to access the services from your machine:

```bash
kubectl port-forward \
  -n microservices service/product-service 8001:8000
```

In a separate terminal:

```bash
curl http://localhost:8001/health
curl http://localhost:8001/products
curl http://localhost:8001/version
```

For Order Service, use another terminal:

```bash
kubectl port-forward \
  -n microservices service/order-service 8002:8000
```

Then test:

```bash
curl http://localhost:8002/health
curl http://localhost:8002/orders/demo
```

Stop port forwarding with `Ctrl+C` when finished.

## Kubernetes Concepts Implemented

### Deployments and Services

- Declarative Deployment and Service manifests.
- ClusterIP Services for internal application access.
- Service discovery using Kubernetes DNS.
- EndpointSlice inspection to verify backend endpoints.
- Self-healing through Deployment-managed Pods.

### Application Configuration

- ConfigMap-based configuration for `PRODUCT_SERVICE_URL`.
- Secret-based environment variable reference for `DB_PASSWORD`.
- Environment-specific configuration without hardcoding the Product Service URL into the Kubernetes manifest.

### Health Checks and Resources

Both application Deployments define:

- HTTP readiness probes using `/health`.
- HTTP liveness probes using `/health`.
- CPU requests of `50m` and memory requests of `64Mi`.
- CPU limits of `500m` and memory limits of `256Mi`.

These settings provide a foundation for scheduling, application health management, and resource-aware scaling.

### Rolling Updates and Rollbacks

Rolling updates and rollback operations have been practiced using Kubernetes Deployments.

Useful commands:

```bash
kubectl rollout status deployment/product-service -n microservices
kubectl rollout history deployment/product-service -n microservices
kubectl rollout undo deployment/product-service -n microservices
```

### Horizontal Pod Autoscaler

The Product Service HPA is defined in `k8s/product-service-hpa.yaml`.

- Minimum replicas: `2`
- Maximum replicas: `4`
- Target average CPU utilization: `50%`

Apply and inspect it:

```bash
kubectl apply -f k8s/product-service-hpa.yaml

kubectl get hpa -n microservices
kubectl describe hpa product-service -n microservices
kubectl top pods -n microservices
```

HPA requires working resource metrics from Metrics Server. The HPA configuration and metrics have been verified in the local lab; successful scale-up under sustained load has not yet been demonstrated.

### Ingress

The Ingress manifest routes requests for `product.local` to Product Service.

File: `k8s/product-ingress.yaml`

This requires a compatible Ingress controller, appropriate local hostname resolution, and cluster access configuration. The manifest alone does not install an Ingress controller.

### Volumes

The `k8s/volume-demo.yaml` manifest demonstrates an `emptyDir` volume mounted at `/data`.

An `emptyDir` volume is temporary storage associated with the lifetime of its Pod. It is useful for understanding shared container storage and ephemeral data, but it is not persistent storage for production workloads.

## Troubleshooting Commands

Inspect Pods and events:

```bash
kubectl get pods -n microservices -o wide
kubectl describe pod <pod-name> -n microservices
kubectl get events -n microservices --sort-by=.metadata.creationTimestamp
```

Inspect logs:

```bash
kubectl logs deployment/product-service -n microservices
kubectl logs deployment/order-service -n microservices
```

Check resource usage:

```bash
kubectl top nodes
kubectl top pods -n microservices
```

Check rollout status:

```bash
kubectl rollout status deployment/product-service -n microservices
kubectl rollout status deployment/order-service -n microservices
```

Common issues include image-tag mismatches, missing ConfigMaps or Secrets, failed health probes, unavailable dependency endpoints, and missing resource metrics.

## Security Notes

- `k8s/app-secret.yaml` is intentionally excluded by `.gitignore`.
- Do not commit real passwords, tokens, cloud credentials, or private keys.
- Kubernetes Secrets are not automatically secure merely because their values are base64-encoded. Production deployments need appropriate access controls and secret-management practices.
- The Metrics Server TLS workaround used in this local lab is not a production configuration.
- This project is a learning environment, not a production-hardened platform.

## Development Roadmap

| Phase | Scope | Status |
|---|---|---|
| 1 | Dockerized FastAPI microservices and Docker Compose | Completed |
| 2 | Kubernetes fundamentals, service discovery, configuration, probes, rollouts, Ingress and volumes | Completed |
| 3 | Resource management, Metrics Server, HPA and reliability concepts | Covered; further load testing planned |
| 4 | CI/CD with GitHub Actions, automated tests, container image publishing and GitOps concepts | Next |
| 5 | Monitoring with Prometheus and Grafana | Planned |
| 6 | Centralized logging and log-based troubleshooting | Planned |
| 7 | Infrastructure as Code with Terraform and deployment on AWS | Planned |
| 8 | Failure simulations, incident troubleshooting and interview preparation | Planned |

Future phases will extend this project toward a more complete DevOps workflow, including automated validation, repeatable infrastructure provisioning, observability, and operational testing.

## Project Goals

This project is intended to demonstrate practical understanding of:

- Containerization and multi-service application architecture.
- Kubernetes deployment, networking, configuration, and scaling.
- Health checks, resource management, and troubleshooting.
- CI/CD and infrastructure automation.
- Monitoring, logging, and reliability engineering.

The project will evolve as each phase is implemented and tested.
