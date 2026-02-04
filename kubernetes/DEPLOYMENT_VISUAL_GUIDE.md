# Kubernetes Deployment File - Component Breakdown

## The 4 Resources in sample-app-deploy.yml

```
sample-app-deploy.yml
│
├── 1. Namespace (springboot-test)
│   └── Creates isolated environment
│
├── 2. Deployment (springbootapi-deployment)
│   ├── Manages Pods
│   ├── Pulls Docker image from Docker Hub
│   ├── Defines resource limits
│   └── Configures health checks
│
├── 3. Service (springbootapi-service)
│   ├── Load balances traffic to pods
│   ├── Provides stable DNS name
│   └── Routes port 8080 to pods
│
└── 4. ServiceMonitor (springbootapi-monitor)
    ├── Configures Prometheus scraping
    ├── Defines metrics endpoint (/metrics)
    └── Sets scrape interval (30s)
```

---

## Visual: How Components Connect

```
┌────────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                          │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │           Namespace: springboot-test                     │ │
│  │                                                          │ │
│  │  ┌─────────────────────────────────────────────────┐   │ │
│  │  │  Deployment: springbootapi-deployment           │   │ │
│  │  │  replicas: 1 (managed by KEDA later)            │   │ │
│  │  │                                                  │   │ │
│  │  │  ┌──────────────────────────────────────────┐  │   │ │
│  │  │  │  Pod 1                                   │  │   │ │
│  │  │  │  ┌────────────────────────────────────┐ │  │   │ │
│  │  │  │  │ Container: springbootapi           │ │  │   │ │
│  │  │  │  │ Image: ajaylk/autoscalex-demo     │ │  │   │ │
│  │  │  │  │ Port: 8080                         │ │  │   │ │
│  │  │  │  │                                    │ │  │   │ │
│  │  │  │  │ Flask app.py running              │ │  │   │ │
│  │  │  │  │   /api/hello                      │ │  │   │ │
│  │  │  │  │   /api/data                       │ │  │   │ │
│  │  │  │  │   /health                         │ │  │   │ │
│  │  │  │  │   /metrics ← Prometheus scrapes   │ │  │   │ │
│  │  │  │  └────────────────────────────────────┘ │  │   │ │
│  │  │  └──────────────┬───────────────────────────┘  │   │ │
│  │  │                 │                              │   │ │
│  │  └─────────────────┼──────────────────────────────┘   │ │
│  │                    │                                  │ │
│  │  ┌─────────────────┴──────────────────────────────┐  │ │
│  │  │  Service: springbootapi-service                │  │ │
│  │  │  DNS: springbootapi-service.springboot-test... │  │ │
│  │  │  Port: 8080 → Pod:8080                         │  │ │
│  │  │  Type: ClusterIP (internal only)               │  │ │
│  │  └──────────────┬─────────────────────────────────┘  │ │
│  │                 │                                    │ │
│  │  ┌──────────────┴─────────────────────────────────┐  │ │
│  │  │  ServiceMonitor: springbootapi-monitor         │  │ │
│  │  │  Scrape: /metrics every 30s                    │  │ │
│  │  └────────────────────────────────────────────────┘  │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

---

## What Each Section Does

### **Namespace**
```yaml
kind: Namespace
metadata:
  name: springboot-test
```
**Think of it as:** A folder that contains all your app resources

### **Deployment**
```yaml
kind: Deployment
spec:
  replicas: 1
  template:
    spec:
      containers:
      - image: ajaylk/autoscalex-demo:latest
```
**Think of it as:** A recipe for creating and managing pods

### **Service**
```yaml
kind: Service
spec:
  selector:
    app: springbootapi
  ports:
  - port: 8080
```
**Think of it as:** A load balancer with a stable DNS name

### **ServiceMonitor**
```yaml
kind: ServiceMonitor
spec:
  endpoints:
  - path: /metrics
    interval: 30s
```
**Think of it as:** Instructions for Prometheus on what to monitor

---

## Key Relationships

### **Labels Connect Everything**

```yaml
# Deployment creates pods WITH this label:
template:
  metadata:
    labels:
      app: springbootapi  ← Label

# Service finds pods BY this label:
selector:
  app: springbootapi  ← Must match!

# ServiceMonitor finds Service BY this label:
selector:
  matchLabels:
    app: springbootapi  ← Must match!
```

**If labels don't match = resources won't connect!**

---

## The Complete Deployment Answer

**To answer your original question:**

```bash
# After creating Dockerfile, you need to:

# 1. Build the image
docker build -t YOUR-USERNAME/autoscalex-demo:latest .

# 2. YES - Push to Docker Hub (required!)
docker login
docker push YOUR-USERNAME/autoscalex-demo:latest

# 3. Create Kubernetes deployment file (✅ Done - sample-app-deploy.yml)

# 4. Update image name in the file
# Change: image: ajaylk/autoscalex-demo:latest
# To:     image: YOUR-USERNAME/autoscalex-demo:latest

# 5. Deploy to cluster
kubectl apply -f kubernetes/sample-app-deploy.yml

# 6. Verify it's running
kubectl get pods -n springboot-test
kubectl port-forward -n springboot-test svc/springbootapi-service 8080:8080
curl http://localhost:8080/api/hello
```

That's the complete workflow! 🎯
