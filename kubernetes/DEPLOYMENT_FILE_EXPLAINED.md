# Kubernetes Deployment File Explanation

## Overview
The `sample-app-deploy.yml` file contains **4 Kubernetes resources**:
1. **Namespace** - Isolated environment for your app
2. **Deployment** - Defines how to run your Flask app
3. **Service** - Exposes your app within the cluster
4. **ServiceMonitor** - Configures Prometheus to scrape metrics

---

## 1. Namespace

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: springboot-test
```

**What it does:**
- Creates an isolated workspace called `springboot-test`
- All your app resources live here
- Provides logical separation from other applications

**Why you need it:**
- Organizes resources
- Prevents naming conflicts
- Allows setting resource quotas per namespace
- Easy cleanup: `kubectl delete namespace springboot-test` removes everything

---

## 2. Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: springbootapi-deployment
  namespace: springboot-test
spec:
  replicas: 1
  selector:
    matchLabels:
      app: springbootapi
  template:
    metadata:
      labels:
        app: springbootapi
    spec:
      containers:
      - name: springbootapi
        image: ajaylk/autoscalex-demo:latest
        ports:
        - containerPort: 8080
        resources: {...}
        livenessProbe: {...}
        readinessProbe: {...}
```

### **Key Components Explained:**

#### **`replicas: 1`**
- Starts with 1 pod initially
- KEDA will modify this based on your autoscaler's predictions
- Can be 0 (no pods) to maxReplicaCount (10 in your case)

#### **`selector.matchLabels`**
- How the Deployment finds its pods
- Must match `template.metadata.labels`
- **Critical:** If these don't match, Deployment won't manage any pods

#### **`image: ajaylk/autoscalex-demo:latest`**
- **⚠️ CHANGE THIS** to your Docker Hub username
- Format: `username/repository:tag`
- `latest` = most recent version
- Can use specific version: `v1.0`, `v2.0`, etc.

#### **`imagePullPolicy: Always`**
- Always pull the latest image from Docker Hub
- Ensures you get updates when you rebuild
- Alternative: `IfNotPresent` (only pull if not cached)

#### **`containerPort: 8080`**
- The port your Flask app listens on inside the container
- Matches `EXPOSE 8080` in Dockerfile
- Matches `app.run(port=8080)` in your Python code

#### **`resources`**
```yaml
resources:
  requests:
    memory: "128Mi"  # Guaranteed memory
    cpu: "100m"      # Guaranteed CPU (0.1 cores)
  limits:
    memory: "256Mi"  # Maximum memory
    cpu: "500m"      # Maximum CPU (0.5 cores)
```

**What this means:**
- **Requests** = Minimum resources Kubernetes reserves
- **Limits** = Maximum resources container can use
- If pod exceeds memory limit → OOMKilled (Out of Memory)
- If pod exceeds CPU limit → Throttled

**Why it matters:**
- Helps Kubernetes schedule pods efficiently
- Prevents one pod from consuming all resources
- Important for cost optimization

#### **`livenessProbe`**
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 10
  failureThreshold: 3
```

**What it does:**
- Checks if your app is **alive**
- Calls `GET /health` every 10 seconds
- If it fails 3 times in a row → Kubernetes **restarts** the pod
- Waits 10 seconds after pod starts before first check

**Flow:**
```
Pod starts → Wait 10s → Check /health → Success? 
                                          ↓ Yes
                                    Wait 10s → Check again
                                          ↓ No
                                    Fail count++
                                          ↓ (After 3 failures)
                                    RESTART POD
```

#### **`readinessProbe`**
```yaml
readinessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
  failureThreshold: 3
```

**What it does:**
- Checks if your app is **ready** to receive traffic
- If it fails → Pod is **removed from Service** (no traffic sent)
- If it succeeds → Pod is **added to Service** (receives traffic)

**Difference from Liveness:**
| Probe | Fails → Action | Use Case |
|-------|----------------|----------|
| **Liveness** | Restart pod | App is frozen/deadlocked |
| **Readiness** | Stop sending traffic | App is starting/busy/loading |

**Example scenario:**
```
Pod starts
  ↓
Liveness: Wait (app might be starting)
Readiness: Check immediately
  ↓ (App not ready yet)
No traffic sent to this pod
  ↓ (After 5 seconds, app ready)
Readiness: Success!
  ↓
Traffic now sent to this pod
```

---

## 3. Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: springbootapi-service
  namespace: springboot-test
spec:
  type: ClusterIP
  selector:
    app: springbootapi
  ports:
  - name: http
    port: 8080
    targetPort: 8080
```

**What it does:**
- Creates a stable DNS name: `springbootapi-service.springboot-test.svc.cluster.local`
- Load balances traffic across all pods with label `app: springbootapi`
- Provides a single entry point

**How traffic flows:**
```
Request → Service (springbootapi-service:8080)
                  ↓
          Load Balancer
         /      |      \
      Pod 1   Pod 2   Pod 3
      :8080   :8080   :8080
```

**Service Types:**
| Type | Description | Access |
|------|-------------|--------|
| **ClusterIP** | Internal only (used here) | Only inside cluster |
| **NodePort** | Exposes on each node's IP | Outside cluster via NodeIP:NodePort |
| **LoadBalancer** | Cloud load balancer | Outside cluster via external IP |

**Why ClusterIP?**
- You access it via `kubectl port-forward` for testing
- Other pods in cluster can access it
- Not exposed to internet (secure)
- Perfect for autoscaling tests

---

## 4. ServiceMonitor

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: springbootapi-monitor
  namespace: springboot-test
  labels:
    release: prmop  # MUST match Prometheus release name
spec:
  selector:
    matchLabels:
      app: springbootapi
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
```

**What it does:**
- Tells Prometheus to scrape metrics from your app
- Finds all Services with label `app: springbootapi`
- Scrapes `http://service:8080/metrics` every 30 seconds
- Stores time-series data for your autoscaler to query

**Critical Label:**
```yaml
labels:
  release: prmop  # Must match your Prometheus Helm release name
```

**How to find your Prometheus release name:**
```bash
helm list -n monitoring
# NAME    NAMESPACE   REVISION    STATUS      CHART
# prmop   monitoring  1           deployed    kube-prometheus-stack-xx.x.x
```

**If your release name is different:**
- Change `release: prmop` to `release: YOUR-RELEASE-NAME`
- Or check Prometheus's ServiceMonitor selector:
  ```bash
  kubectl get prometheus -n monitoring -o yaml | grep serviceMonitorSelector -A 5
  ```

---

## How to Deploy This File

### **Step 1: Update Image Name**

Open `sample-app-deploy.yml` and replace line 32:
```yaml
image: ajaylk/autoscalex-demo:latest
```
With your Docker Hub username:
```yaml
image: YOUR-USERNAME/autoscalex-demo:latest
```

### **Step 2: Apply to Kubernetes**

```bash
# Deploy everything
kubectl apply -f kubernetes/sample-app-deploy.yml

# Expected output:
# namespace/springboot-test created
# deployment.apps/springbootapi-deployment created
# service/springbootapi-service created
# servicemonitor.monitoring.coreos.com/springbootapi-monitor created
```

### **Step 3: Verify Deployment**

```bash
# Check namespace
kubectl get namespace springboot-test

# Check deployment
kubectl get deployment -n springboot-test

# Check pods
kubectl get pods -n springboot-test

# Check service
kubectl get svc -n springboot-test

# Check ServiceMonitor
kubectl get servicemonitor -n springboot-test
```

---

## Detailed Verification Steps

### **1. Check Pod Status**

```bash
kubectl get pods -n springboot-test

# Expected:
# NAME                                        READY   STATUS    RESTARTS   AGE
# springbootapi-deployment-xxxxxxxxxx-xxxxx   1/1     Running   0          30s
```

**Possible statuses:**
| Status | Meaning | Action |
|--------|---------|--------|
| `Running` | ✅ Working | All good! |
| `Pending` | Scheduling | Wait a bit |
| `ImagePullBackOff` | Can't download image | Check image name, Docker Hub |
| `CrashLoopBackOff` | App keeps crashing | Check logs: `kubectl logs <pod-name> -n springboot-test` |
| `CreateContainerConfigError` | Configuration error | Check deployment.yaml syntax |

### **2. Check Detailed Pod Info**

```bash
# Get detailed information
kubectl describe pod -n springboot-test <pod-name>

# Look for:
# - Events section (shows what happened)
# - Conditions section (shows pod health)
# - Container status
```

### **3. Check Application Logs**

```bash
# View logs
kubectl logs -n springboot-test deployment/springbootapi-deployment

# Follow logs in real-time
kubectl logs -n springboot-test deployment/springbootapi-deployment -f

# Expected output:
# * Serving Flask app 'app'
# * Running on all addresses (0.0.0.0)
# * Running on http://127.0.0.1:8080
```

### **4. Test the Application**

```bash
# Port-forward to access locally
kubectl port-forward -n springboot-test svc/springbootapi-service 8080:8080

# In another terminal:
curl http://localhost:8080/api/hello
curl http://localhost:8080/api/data
curl http://localhost:8080/health
curl http://localhost:8080/metrics
```

### **5. Verify Prometheus is Scraping**

```bash
# Port-forward Prometheus (if installed)
kubectl port-forward -n monitoring svc/prmop-kube-prometheus-prometheus 9090:9090

# Open browser: http://localhost:9090/targets
# Look for: springboot-test/springbootapi-monitor/0
# Status should be "UP" (green)
```

---

## Troubleshooting Common Issues

### **Issue: ImagePullBackOff**

```bash
# Check the exact error
kubectl describe pod -n springboot-test <pod-name> | grep -A 10 Events

# Common causes:
# 1. Image doesn't exist on Docker Hub
# 2. Typo in image name
# 3. Repository is private (need imagePullSecrets)
```

**Solution:**
```bash
# Verify image exists
docker pull YOUR-USERNAME/autoscalex-demo:latest

# If private repository, create secret:
kubectl create secret docker-registry regcred \
  --docker-server=https://index.docker.io/v1/ \
  --docker-username=YOUR-USERNAME \
  --docker-password=YOUR-PASSWORD \
  -n springboot-test

# Add to deployment under spec.template.spec:
# imagePullSecrets:
#   - name: regcred
```

### **Issue: CrashLoopBackOff**

```bash
# Check why it's crashing
kubectl logs -n springboot-test <pod-name>

# Common causes:
# 1. Missing Python dependencies
# 2. Syntax error in app.py
# 3. Port already in use (unlikely in container)
```

### **Issue: Service Not Accessible**

```bash
# Check if Service has endpoints
kubectl get endpoints -n springboot-test

# Should show pod IPs:
# NAME                      ENDPOINTS          AGE
# springbootapi-service     10.244.0.5:8080    1m

# If no endpoints, selector might be wrong
kubectl get svc springbootapi-service -n springboot-test -o yaml
kubectl get pods -n springboot-test --show-labels
```

---

## Understanding the Complete Flow

```
┌───────────────────────────────────────────────────────┐
│ 1. kubectl apply -f sample-app-deploy.yml            │
└───────────────────────────────────────────────────────┘
                        ↓
┌───────────────────────────────────────────────────────┐
│ 2. Kubernetes creates Namespace                       │
│    - springboot-test namespace is created             │
└───────────────────────────────────────────────────────┘
                        ↓
┌───────────────────────────────────────────────────────┐
│ 3. Kubernetes creates Deployment                      │
│    - Reads spec: replicas=1, image=ajaylk/...        │
│    - Pulls image from Docker Hub                      │
│    - Creates 1 pod                                    │
└───────────────────────────────────────────────────────┘
                        ↓
┌───────────────────────────────────────────────────────┐
│ 4. Pod starts                                         │
│    - Container starts running                         │
│    - Flask app starts on port 8080                   │
│    - Waits 10s, then checks liveness probe           │
│    - Waits 5s, then checks readiness probe           │
└───────────────────────────────────────────────────────┘
                        ↓
┌───────────────────────────────────────────────────────┐
│ 5. Kubernetes creates Service                         │
│    - Finds pods with label app=springbootapi         │
│    - Creates endpoint: springbootapi-service:8080    │
│    - Routes traffic to pod(s)                        │
└───────────────────────────────────────────────────────┘
                        ↓
┌───────────────────────────────────────────────────────┐
│ 6. Prometheus Operator creates ServiceMonitor        │
│    - Finds Service with label app=springbootapi      │
│    - Configures Prometheus to scrape /metrics        │
│    - Scrapes every 30 seconds                        │
└───────────────────────────────────────────────────────┘
                        ↓
┌───────────────────────────────────────────────────────┐
│ 7. Your app is now running and monitored!            │
│    - Accessible via Service DNS name                  │
│    - Metrics being collected by Prometheus           │
│    - Ready for KEDA autoscaling                      │
└───────────────────────────────────────────────────────┘
```

---

## Customization Options

### **Adjust Resource Limits**

If your app needs more resources:
```yaml
resources:
  requests:
    memory: "256Mi"  # Double the memory
    cpu: "200m"      # Double the CPU
  limits:
    memory: "512Mi"
    cpu: "1000m"     # 1 full CPU core
```

### **Change Initial Replicas**

```yaml
replicas: 3  # Start with 3 pods instead of 1
```

### **Add Environment Variables**

```yaml
env:
- name: LOG_LEVEL
  value: "DEBUG"
- name: DATABASE_URL
  value: "postgres://..."
- name: SECRET_KEY
  valueFrom:
    secretKeyRef:
      name: app-secrets
      key: secret-key
```

### **Change Probe Intervals**

For faster detection:
```yaml
livenessProbe:
  periodSeconds: 5     # Check every 5 seconds instead of 10
  failureThreshold: 2  # Restart after 2 failures instead of 3
```

### **Use a Specific Image Version**

Instead of `latest`:
```yaml
image: ajaylk/autoscalex-demo:v1.0.0
```

**Best practice:** Use specific versions in production, `latest` for development

---

## Deploy Command Options

### **Basic Deployment**
```bash
kubectl apply -f kubernetes/sample-app-deploy.yml
```

### **Deployment with Namespace Creation (if namespace doesn't exist)**
```bash
kubectl create namespace springboot-test
kubectl apply -f kubernetes/sample-app-deploy.yml
```

### **Dry-Run (Preview without applying)**
```bash
kubectl apply -f kubernetes/sample-app-deploy.yml --dry-run=client
# Shows what would be created without actually creating it
```

### **Deployment with Validation**
```bash
kubectl apply -f kubernetes/sample-app-deploy.yml --validate=true
```

### **View Generated Resources**
```bash
kubectl apply -f kubernetes/sample-app-deploy.yml -o yaml
# Shows the complete resource definitions
```

---

## Update/Rollout Commands

### **After Rebuilding Your Docker Image**

```bash
# 1. Build new image
docker build -t YOUR-USERNAME/autoscalex-demo:latest sample_app/

# 2. Push to Docker Hub
docker push YOUR-USERNAME/autoscalex-demo:latest

# 3. Force Kubernetes to pull new image
kubectl rollout restart deployment/springbootapi-deployment -n springboot-test

# 4. Watch the rollout
kubectl rollout status deployment/springbootapi-deployment -n springboot-test

# 5. Verify new pods are running
kubectl get pods -n springboot-test
```

### **Rollback if Something Breaks**

```bash
# Undo last deployment
kubectl rollout undo deployment/springbootapi-deployment -n springboot-test

# Rollback to specific revision
kubectl rollout history deployment/springbootapi-deployment -n springboot-test
kubectl rollout undo deployment/springbootapi-deployment -n springboot-test --to-revision=2
```

---

## Clean Up

### **Delete Everything**
```bash
# Delete all resources in the file
kubectl delete -f kubernetes/sample-app-deploy.yml

# Or delete the entire namespace (removes everything)
kubectl delete namespace springboot-test
```

### **Delete Specific Resources**
```bash
# Delete only deployment
kubectl delete deployment springbootapi-deployment -n springboot-test

# Delete only service
kubectl delete service springbootapi-service -n springboot-test

# Delete only ServiceMonitor
kubectl delete servicemonitor springbootapi-monitor -n springboot-test
```

---

## Quick Reference

### **Full Deployment Workflow**

```bash
# 1. Build image
cd sample_app
docker build -t YOUR-USERNAME/autoscalex-demo:latest .

# 2. Test locally
docker run -d -p 8080:8080 --name test YOUR-USERNAME/autoscalex-demo:latest
curl http://localhost:8080/api/hello
docker stop test && docker rm test

# 3. Push to Docker Hub
docker login
docker push YOUR-USERNAME/autoscalex-demo:latest

# 4. Update deployment file
# Edit kubernetes/sample-app-deploy.yml - change image name

# 5. Deploy to Kubernetes
cd ..
kubectl apply -f kubernetes/sample-app-deploy.yml

# 6. Verify
kubectl get all -n springboot-test

# 7. Test in cluster
kubectl port-forward -n springboot-test svc/springbootapi-service 8080:8080
curl http://localhost:8080/api/hello

# 8. Check logs
kubectl logs -n springboot-test deployment/springbootapi-deployment -f
```

---

## Next Steps After Deployment

1. **Verify Prometheus scraping**: Check http://localhost:9090/targets
2. **Deploy TSF autoscaler**: Similar process for your autoscaler image
3. **Deploy ScaledObject**: Apply KEDA configuration
4. **Generate load**: Create traffic to trigger autoscaling
5. **Monitor**: Watch pods scale up/down

The deployment file is now ready to use! Just update the image name and apply it. 🚀
