# EKS GitOps Pipeline — Jenkins → ECR → ArgoCD → EKS

A small end-to-end DevOps pipeline: a Flask app is built, scanned, containerized, and
shipped to an EKS cluster through a GitOps flow, with Prometheus and Grafana wired up
for metrics.

## Architecture

```
 developer push
       │
       ▼
   Jenkins CI ──► pytest ──► SonarQube scan ──► Docker build ──► push to ECR
       │
       ▼
 update image tag in GitOps config repo (k8s/deployment.yaml)
       │
       ▼
   ArgoCD (watching the GitOps repo) ──► syncs ──► EKS cluster
                                                        │
                                                        ▼
                                          Pod exposes /metrics ──► Prometheus ──► Grafana
```

Jenkins never talks to the cluster directly — it only updates the GitOps repo.
ArgoCD is the only thing with cluster access, which keeps deploy credentials out of CI.

## What's in this repo

| Path | Purpose |
|---|---|
| `app/` | Flask app with `/health` and `/metrics` endpoints |
| `Dockerfile` | Multi-stage build, runs as non-root, has a `HEALTHCHECK` |
| `Jenkinsfile` | CI pipeline: test → SonarQube scan → quality gate → build → push to ECR → update GitOps repo |
| `k8s/deployment.yaml` | Deployment manifest (2 replicas, resource limits, readiness/liveness probes) |
| `k8s/service.yaml` | ClusterIP service in front of the pods |
| `k8s/servicemonitor.yaml` | Tells the Prometheus Operator to scrape `/metrics` |
| `argocd/application.yaml` | ArgoCD Application — auto-syncs the `k8s/` manifests from the GitOps repo onto EKS |
| `monitoring/` | Local `docker-compose` stack (app + Prometheus + Grafana) for testing metrics without a cluster |

## Running it locally (no cluster needed)

```bash
docker compose -f monitoring/docker-compose.monitoring.yml up --build
```

- App: http://localhost:5000
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (login `admin` / `admin`)

## Deploying to EKS

1. Build and push the image to ECR (or let Jenkins do it — see `Jenkinsfile`).
2. Apply the base manifests once:
   ```bash
   kubectl create namespace demo
   kubectl apply -f k8s/deployment.yaml
   kubectl apply -f k8s/service.yaml
   ```
3. Install the [kube-prometheus-stack](https://github.com/prometheus-community/helm-charts) if it isn't already on the cluster, then apply the `ServiceMonitor`:
   ```bash
   kubectl apply -f k8s/servicemonitor.yaml
   ```
4. Point ArgoCD at this repo so future changes deploy automatically:
   ```bash
   kubectl apply -f argocd/application.yaml
   ```

From here, every merge that updates the image tag in `k8s/deployment.yaml` is picked
up by ArgoCD's auto-sync — no manual `kubectl apply` needed after the first setup.

## Notes / what I'd add next

- IAM Roles for Service Accounts (IRSA) instead of node-level IAM permissions
- A Helm chart instead of raw manifests, for templating across environments
- Horizontal Pod Autoscaler tied to the custom `app_requests_total` metric
- Ansible playbook for bootstrapping the EKS node group's baseline config

## Stack

Docker · Kubernetes (EKS) · Jenkins · SonarQube · ArgoCD · Prometheus · Grafana
