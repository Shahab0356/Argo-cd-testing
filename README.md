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



I’ll explain each step conceptually + provide exact commands (ready to copy-paste).

🧩 Step 1: Create the EKS Cluster (Control Plane)
🎯 Purpose

This step creates:

The EKS control plane (API server, etcd)

A VPC with public and private subnets (if not existing)

IAM roles and security groups for EKS

✅ Command
eksctl create cluster \
  --name flask-eks-test-1 \
  --region us-east-1 \
  --version 1.32 \
  --vpc-nat-mode Single \
  --without-nodegroup \
  --tags "Project=FlaskApp,Owner=DevOps,Environment=Test"

🧠 Explanation
Flag	Description
--name	Name of your cluster
--region	AWS region
--version	Kubernetes version (use latest stable 1.32)
--without-nodegroup	Creates control plane only (we’ll add nodes in step 3)
--vpc-nat-mode Single	Creates one NAT gateway (cheaper for test setups)
--tags	Adds metadata for cost tracking

🕐 This command takes about 10–15 minutes to complete.

✅ When done, you’ll have:

An active EKS cluster.

A dedicated VPC.

Subnets and IAM roles created by eksctl.

You can verify:

eksctl get cluster --region us-east-1

🧩 Step 2: Associate the OIDC Provider
🎯 Purpose

The OIDC provider allows Kubernetes service accounts to assume AWS IAM roles.
It’s required for features like:

ALB Ingress Controller

External DNS

EBS CSI driver

App Mesh

Any AWS-integrated service account-based access

✅ Command
eksctl utils associate-iam-oidc-provider \
  --cluster flask-eks-test-1 \
  --region us-east-1 \
  --approve


✅ This links your cluster with AWS IAM OIDC and lets pods authenticate securely without storing AWS credentials inside containers.

You can verify:

aws eks describe-cluster \
  --name flask-eks-test-1 \
  --region us-east-1 \
  --query "cluster.identity.oidc.issuer" \
  --output text


You should see an output like:

https://oidc.eks.us-east-1.amazonaws.com/id/xxxxxxxxxxxxxxxxxxxx

🧱 Step 3: Create Node Group (Your Step)

Once Steps 1 and 2 are done successfully, run your existing command:

eksctl create nodegroup \
    --cluster flask-eks-test-1 \
    --region us-east-1 \
    --name eksdemo1-ng-public2 \
    --node-type t3.micro \
    --nodes 2 \
    --nodes-min 2 \
    --nodes-max 2 \
    --node-volume-size 20 \
    --ssh-access \
    --ssh-public-key nayapay-1 \
    --managed \
    --asg-access \
    --external-dns-access \
    --full-ecr-access \
    --appmesh-access \
    --alb-ingress-access \
    --tags "Project=FlaskApp,Owner=DevOps,Environment=Test"

🧠 Summary of Full Workflow
Step	Action	Command Summary
1	Create Cluster (Control Plane)	eksctl create cluster --without-nodegroup
2	Associate OIDC Provider	eksctl utils associate-iam-oidc-provider --approve
3	Create Node Group	eksctl create nodegroup --managed ...












IN ONE SHOT 

eksctl create cluster \
  --name flask-eks-test-1 \
  --region us-east-1 \
  --version 1.32 \
  --vpc-nat-mode Single \
  --without-nodegroup \
  --tags "Project=FlaskApp,Owner=DevOps,Environment=Test" && \
eksctl utils associate-iam-oidc-provider \
  --cluster flask-eks-test-1 \
  --region us-east-1 \
  --approve && \
eksctl create nodegroup \
  --cluster flask-eks-test-1 \
  --region us-east-1 \
  --name eksdemo1-ng-public2 \
  --node-type t3.micro \
  --nodes 2 \
  --nodes-min 2 \
  --nodes-max 2 \
  --node-volume-size 20 \
  --ssh-access \
  --ssh-public-key nayapay-1 \
  --managed \
  --asg-access \
  --external-dns-access \
  --full-ecr-access \
  --appmesh-access \
  --alb-ingress-access \
  --tags "Project=FlaskApp,Owner=DevOps,Environment=Test"









  # 🚀 Flask EKS Demo Application — CI/CD with GitHub Actions, ECR & EKS

This project demonstrates a **complete DevOps pipeline** for deploying a **Python Flask** application to **Amazon EKS (Elastic Kubernetes Service)** using **GitHub Actions**, **Docker**, and **Amazon ECR**.

It is built to show a **real-world, production-ready CI/CD workflow** — from code push to automated deployment in Kubernetes.

---

## 🏗️ Project Architecture

