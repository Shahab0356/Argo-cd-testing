# 🧠 EKS + Flask + ALB + Monitoring Stack

This project deploys a Flask application to an AWS EKS cluster, exposes it via an ALB Ingress, and sets up full observability using Prometheus, Grafana, and Blackbox Exporter. Ideal for modular cloud-native deployments with built-in monitoring and alerting.

---

## 🚀 Workflow Summary

### 1. Build & Push Docker Image
- Build Flask app image locally  
- Push to AWS ECR

### 2. Create EKS Cluster
- Provision EKS via `eksctl` or AWS Console  
- Configure `kubectl` access

### 3. Deploy App to Kubernetes
- Create namespace  
- Apply Deployment, Service, and HPA  
- Validate pods and service

### 4. Configure ALB Ingress
- Define Ingress with ALB annotations  
- Apply manifest to trigger ALB provisioning

### 5. Install AWS Load Balancer Controller
- Enable IAM OIDC provider  
- Create IAM role and service account  
- Install controller via Helm

### 6. Validate ALB & Test Endpoint
- Confirm ALB DNS via `kubectl get ingress`  
- Test app via browser or `curl`

---

## 🔧 Key Commands

```bash
# Build and push image
docker build -t flask-app .
docker tag flask-app:latest <your-ecr-uri>:latest
docker push <your-ecr-uri>:latest

# Apply Kubernetes manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/ingress.yaml

# Install ALB Controller via Helm
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=eks-demo-cluster \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller \
  --set region=us-east-1 \
  --set vpcId=<your-vpc-id>


Observability & Monitoring Setup
7. Install kube-prometheus-stack
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace

8. Expose Grafana via NodePort
kubectl patch svc kube-prometheus-stack-grafana -n monitoring \
  -p '{"spec": {"type": "NodePort"}}'
kubectl get svc kube-prometheus-stack-grafana -n monitoring
Access Grafana at: http://<node-ip>:<node-port>

9. Monitor Flask App with Prometheus
Ensure your Flask app exposes /metrics endpoint. Then:
Create a Service exposing port 5000
Create a ServiceMonitor in monitoring namespace:
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: eks-demo-app-monitor
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: eks-demo-app
  namespaceSelector:
    matchNames:
      - eks-demo-app
  endpoints:
    - port: http
      path: /metrics
      interval: 30s

10. External Monitoring with Blackbox Exporter
Install Blackbox Exporter via Helm, then create a probe:
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: eks-demo-app-http
  namespace: monitoring
spec:
  jobLabel: eks-demo-app-http
  endpoints:
    - port: http
      path: /probe
      params:
        module: [http_2xx]
        target: [http://<your-alb-dns>]
      interval: 30s
  selector:
    matchLabels:
      app.kubernetes.io/name: prometheus-blackbox-exporter


🧪 Validation & Troubleshooting
Prometheus
Access UI via port-forward: kubectl port-forward svc/kube-prometheus-stack-prometheus 9090 -n monitoring

Check /targets for scrape status

Common errors:

exceeded sample limit: reduce cardinality

duplicate timestamp: fix exporter config

out of bounds: sync node clocks

Grafana
Default credentials: admin / prom-operator

Import dashboards:

Prometheus Stats: ID 3662

Blackbox Exporter: ID 13659

Useful metrics:

probe_success{job="eks-demo-app-http"}

http_requests_total

📣 Alerting (Optional)
Add Prometheus alert rules:
- alert: ALBProbeDown
  expr: probe_success{job="eks-demo-app-http"} == 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "ALB probe failed for eks-demo-app"

📚 Notes
Always validate resource names, labels, and selectors
Document every manifest and config for future onboarding
Use kubectl describe, logs, and events for debugging
Modularize Helm values and manifests for reuse
Let me know if you want this saved as a GitHub Gist, embedded into your repo, or split into multiple files like `README.md`, `monitoring.md`, and `alerts.md`. You’ve got a production-grade blueprint now — ready to scale, reset, or onboard anyone.














own notes.
name = eks-demo-app
AWS account : 052988671062
ecr image : eks-demo-app:latest
<your-alb-role> with the name of the IAM role you created (e.g. ShahabALBRole)
create new eks

eksctl create cluster --name eks-demo-app-cluster --region us-east-1 --nodegroup-name eks-demo-app-nodes --nodes 3 --node-type t3.medium --zones "us-east-1a" --with-oidc --managed --ssh-access --ssh-public-key kube-demo --tags "project=eks-demo-app,owner=shahab" --version 1.32