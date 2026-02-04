# Kubernetes Deployment File - Complete Explanation

## What is a Kubernetes Deployment?

A **Deployment** is a Kubernetes resource that:
- Defines how to run your application
- Manages multiple copies (replicas) of your app
- Handles updates and rollbacks
- Ensures desired number of pods are always running

**Think of it as:** A supervisor that makes sure your app is always running with the right number of copies.

---

## Line-by-Line Breakdown

### **Line 1: Document Separator**
```yaml
---
```
- Optional YAML document separator
- Allows multiple resources in one file
- Useful when combining Deployment + Service in one file

---

### **Line 2-3: Resource Type**
```yaml
apiVersion: apps/v1
kind: Deployment
```

#### **`apiVersion: apps/v1`**
- Specifies which Kubernetes API version to use
- `apps/v1` is the API group for Deployments
- Different resources use different API versions:
  - Pods: `v1`
  - Deployments: `apps/v1`
  - Services: `v1`
  - Ingress: `networking.k8s.io/v1`

**Why it matters:** Ensures compatibility with your Kubernetes cluster version

#### **`kind: Deployment`**
- Tells Kubernetes what type of resource this is
- Other kinds: `Pod`, `Service`, `ConfigMap`, `Secret`, etc.
- Determines what fields are available in `spec`

---

### **Line 4-5: Metadata**
```yaml
metadata:
  name: sample-flask-app
```

#### **`metadata`**
- Data about the resource (not the pods)
- Contains: name, labels, annotations, namespace

#### **`name: sample-flask-app`**
- **Unique identifier** for this Deployment
- Must be unique within the namespace
- Used in commands: `kubectl get deployment sample-flask-app`
- Can contain: lowercase letters, numbers, hyphens (-)
- Cannot contain: spaces, uppercase letters, underscores

**Examples:**
- ✅ `sample-flask-app`
- ✅ `my-app-v2`
- ✅ `api-server-123`
- ❌ `Sample_Flask_App` (uppercase & underscore)
- ❌ `my app` (space)

---

### **Line 6: Spec (Specification)**
```yaml
spec:
```

- **Short for "specification"**
- Defines the desired state of the Deployment
- Contains: replicas, selector, template
- Kubernetes will work to make actual state match this desired state

---

### **Line 7-9: Selector**
```yaml
selector:
  matchLabels:
    app: flask-app
```

#### **`selector`**
- **How the Deployment finds its pods**
- Critical for connecting Deployment to Pods
- Must match the labels in `template.metadata.labels`

#### **`matchLabels`**
- Key-value pairs that must match pod labels
- Can have multiple labels:
  ```yaml
  matchLabels:
    app: flask-app
    environment: production
    version: v1
  ```

**How it works:**
```
Deployment (selector: app=flask-app)
         ↓ (searches for)
    Pod 1 (labels: app=flask-app) ✅ Matched!
    Pod 2 (labels: app=other-app) ❌ Not matched
    Pod 3 (labels: app=flask-app) ✅ Matched!
```

**⚠️ Common Mistake:**
```yaml
selector:
  matchLabels:
    app: flask-app  ← This

template:
  metadata:
    labels:
      app: DIFFERENT-NAME  ← Must be the same!
```
If these don't match, you'll get an error!

---

### **Line 10: Replicas**
```yaml
replicas: 1
```

#### **`replicas: 1`**
- **How many copies (pods) to run**
- `1` = One pod running
- `3` = Three identical pods running
- `0` = No pods (app is stopped)

**What happens:**
- Kubernetes creates exactly this many pods
- If a pod dies, Kubernetes creates a new one to maintain count
- When KEDA autoscales, it modifies this number

**Examples:**
```yaml
replicas: 1   # Single pod (development/testing)
replicas: 3   # High availability (production)
replicas: 10  # High traffic handling
replicas: 0   # Paused/stopped
```

**During autoscaling:**
```
Time  | Replicas | Reason
------|----------|--------
0:00  | 1        | Initial state
0:05  | 3        | KEDA detected increased load
0:10  | 7        | Load keeps increasing
0:15  | 4        | Load decreased
0:20  | 1        | Back to baseline
```

---

### **Line 11-14: Pod Template**
```yaml
template:
  metadata:
    labels:
      app: flask-app
```

#### **`template`**
- **Blueprint for creating pods**
- Every pod created by this Deployment follows this template
- Contains: metadata and spec for pods

#### **`template.metadata.labels`**
- Labels attached to every pod
- **MUST match** `selector.matchLabels`
- Used by Service to find pods
- Used by KEDA to identify what to scale

**Think of labels as:** Sticky notes on pods that say "I belong to flask-app"

---

### **Line 15-16: Container Spec**
```yaml
spec:
  containers:
  - name: sample-flask-app
```

#### **`spec` (inside template)**
- Defines what runs inside the pod
- Contains: containers, volumes, service account, etc.

#### **`containers`**
- **List of containers** to run in the pod
- Usually 1 container per pod (your Flask app)
- Can have multiple (sidecar pattern):
  ```yaml
  containers:
  - name: app
    image: my-app:latest
  - name: logging-sidecar
    image: fluent-bit:latest
  ```

#### **`- name: sample-flask-app`**
- Name of this container within the pod
- Used in logs: `kubectl logs pod-name -c sample-flask-app`
- Must be unique within the pod
- Doesn't need to match anything else

---

### **Line 18: Docker Image**
```yaml
image: wolfycodes4fun/python-sample-demo:latest
```

#### **`image`**
- **The Docker image to run**
- Format: `registry/username/repository:tag`
- Examples:
  ```yaml
  image: nginx:latest                           # Docker Hub official
  image: ajaylk/autoscalex-demo:latest         # Docker Hub user
  image: ajaylk/autoscalex-demo:v1.0.0         # Specific version
  image: gcr.io/my-project/my-app:latest       # Google Container Registry
  image: myregistry.azurecr.io/app:latest      # Azure Container Registry
  ```

**Image components:**
```
wolfycodes4fun / python-sample-demo : latest
      ↑                 ↑              ↑
  Username          Repository        Tag
```

**Tags explained:**
- `latest` = Most recent build (default)
- `v1.0.0` = Specific version
- `dev` = Development version
- `stable` = Stable release

**⚠️ Important:** You MUST change this to your own image!

---

### **Line 19-20: Container Port**
```yaml
ports:
- containerPort: 8080
```

#### **`ports`**
- List of ports the container exposes
- Informational (like `EXPOSE` in Dockerfile)
- Used by Service to know which port to target

#### **`containerPort: 8080`**
- The port your Flask app listens on **inside the container**
- Must match your app.py: `app.run(port=8080)`
- Must match Dockerfile: `EXPOSE 8080`

**Can specify multiple ports:**
```yaml
ports:
- containerPort: 8080
  name: http
  protocol: TCP
- containerPort: 9090
  name: metrics
  protocol: TCP
```

**With names:**
```yaml
ports:
- containerPort: 8080
  name: http        # Service can reference by name
  protocol: TCP     # TCP or UDP
```

---

## Complete Annotated Example

```yaml
---
# YAML document separator
apiVersion: apps/v1              # API version for Deployments
kind: Deployment                 # Type of resource

metadata:                        # Information ABOUT the Deployment
  name: sample-flask-app         # Name of the Deployment object
  namespace: springboot-test     # Which namespace it lives in (optional, defaults to 'default')
  labels:                        # Labels on the Deployment itself (optional)
    app: flask-app
    version: v1
    team: dev

spec:                            # DESIRED STATE of the Deployment
  replicas: 1                    # How many pods to run
  
  selector:                      # HOW to find pods managed by this Deployment
    matchLabels:
      app: flask-app             # Find pods with this label
      
  template:                      # BLUEPRINT for creating pods
    metadata:                    # Metadata for the PODS
      labels:
        app: flask-app           # Labels on each pod (MUST match selector!)
        version: v1
    
    spec:                        # SPEC for the PODS
      containers:                # List of containers in each pod
      - name: sample-flask-app   # Container name (for logs)
        image: wolfycodes4fun/python-sample-demo:latest  # Docker image to run
        
        imagePullPolicy: Always  # When to pull image: Always, IfNotPresent, Never
        
        ports:                   # Ports the container exposes
        - containerPort: 8080    # Your Flask app's port
          name: http             # Name for this port (used by Service)
          protocol: TCP          # TCP or UDP
        
        env:                     # Environment variables
        - name: PORT
          value: "8080"
        - name: LOG_LEVEL
          value: "INFO"
        
        resources:               # CPU and memory limits
          requests:              # Minimum guaranteed
            memory: "128Mi"
            cpu: "100m"
          limits:                # Maximum allowed
            memory: "256Mi"
            cpu: "500m"
        
        livenessProbe:           # Is the app alive?
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 10
          failureThreshold: 3
        
        readinessProbe:          # Is the app ready for traffic?
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
          failureThreshold: 3
```

---

## Key Concepts Explained

### **1. Deployment vs Pod vs Container**

```
Deployment (sample-flask-app)
    ↓ (manages)
  Pods (creates/deletes them)
    ↓ (runs)
  Containers (your Flask app)
```

**Hierarchy:**
- **Deployment** = Manager (ensures replicas are running)
- **Pod** = Wrapper (can contain 1+ containers)
- **Container** = Your actual app (Docker container)

### **2. Labels and Selectors**

**Labels** = Tags you put on resources
**Selectors** = Queries to find resources by labels

```yaml
# Deployment says: "I manage pods with app=flask-app"
selector:
  matchLabels:
    app: flask-app

# Pods say: "My label is app=flask-app"
template:
  metadata:
    labels:
      app: flask-app

# Result: Deployment manages these pods ✅
```

**Why labels matter:**
- Deployments find their pods using labels
- Services find pods using labels
- KEDA finds what to scale using labels
- You query pods using labels: `kubectl get pods -l app=flask-app`

### **3. Desired State vs Actual State**

Kubernetes constantly works to match actual state to desired state:

```
Desired State (in YAML)         Actual State (in cluster)
replicas: 3                     Currently: 1 pod
    ↓                               ↓
Kubernetes sees mismatch
    ↓
Creates 2 more pods
    ↓
Actual State: 3 pods ✅
```

**Another example:**
```
Desired: replicas: 3
Actual: 3 pods running

One pod crashes
    ↓
Actual: 2 pods running
    ↓
Kubernetes detects mismatch
    ↓
Creates 1 new pod
    ↓
Actual: 3 pods running ✅
```

---

## Field Reference Guide

### **Required Fields** (Must have these)

| Field | Purpose | Example |
|-------|---------|---------|
| `apiVersion` | API version | `apps/v1` |
| `kind` | Resource type | `Deployment` |
| `metadata.name` | Unique name | `my-app` |
| `spec.selector` | How to find pods | `matchLabels: {app: my-app}` |
| `spec.template` | Pod blueprint | See template section |
| `spec.template.metadata.labels` | Pod labels | `app: my-app` |
| `spec.template.spec.containers` | Container list | Array of containers |
| `spec.template.spec.containers[0].name` | Container name | `my-container` |
| `spec.template.spec.containers[0].image` | Docker image | `user/image:tag` |

**⚠️ Critical Rule:** `spec.selector.matchLabels` MUST match `spec.template.metadata.labels`

---

### **Optional But Recommended Fields**

| Field | Purpose | Default | Recommendation |
|-------|---------|---------|----------------|
| `spec.replicas` | Number of pods | 1 | Set to 1 for KEDA |
| `metadata.namespace` | Which namespace | `default` | Always specify |
| `spec.template.spec.containers[].ports` | Container ports | None | Always define |
| `spec.template.spec.containers[].resources` | CPU/Memory | No limits | Always set |
| `spec.template.spec.containers[].livenessProbe` | Health check | None | Recommended |
| `spec.template.spec.containers[].readinessProbe` | Ready check | None | Recommended |
| `spec.template.spec.containers[].env` | Environment vars | None | As needed |

---

## Your Current File - What's Missing?

### **What You Have ✅**
- Basic deployment structure
- Container specification
- Port definition
- Correct selector/labels match

### **What's Missing (Should Add) ⚠️**

#### **1. Namespace**
```yaml
metadata:
  name: sample-flask-app
  namespace: springboot-test  # Add this!
```

#### **2. Resource Limits**
```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "500m"
```

#### **3. Health Probes**
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
```

#### **4. ImagePullPolicy**
```yaml
imagePullPolicy: Always  # Ensures latest image is pulled
```

---

## Improved Version of Your Deployment

Here's your deployment with recommended additions:

```yaml
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sample-flask-app
  namespace: springboot-test  # ADDED
  labels:                     # ADDED
    app: flask-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: flask-app
  template:
    metadata:
      labels:
        app: flask-app
    spec:
      containers:
      - name: sample-flask-app
        image: wolfycodes4fun/python-sample-demo:latest
        imagePullPolicy: Always  # ADDED
        
        ports:
        - containerPort: 8080
          name: http             # ADDED
          protocol: TCP          # ADDED
        
        # ADDED: Resource limits
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "500m"
        
        # ADDED: Health checks
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
```

---

## Common Field Values Explained

### **replicas:**
```yaml
replicas: 1   # Development: 1 pod
replicas: 3   # Production: 3 pods (high availability)
replicas: 0   # Stopped: no pods running
```

### **imagePullPolicy:**
```yaml
Always       # Always pull from registry (good for 'latest' tag)
IfNotPresent # Pull only if not in local cache (good for versioned tags)
Never        # Never pull, must exist locally
```

### **protocol:**
```yaml
TCP   # Most HTTP/gRPC services (default)
UDP   # DNS, streaming, gaming
```

### **Resource units:**
```yaml
# CPU:
"100m"  # 100 millicores = 0.1 CPU
"500m"  # 500 millicores = 0.5 CPU  
"1"     # 1 full CPU core
"2.5"   # 2.5 CPU cores

# Memory:
"128Mi"   # 128 Mebibytes (134 MB)
"256Mi"   # 256 Mebibytes (268 MB)
"1Gi"     # 1 Gibibyte (1.07 GB)
"500M"    # 500 Megabytes (decimal)
```

---

## How Kubernetes Uses This File

### **When you run: `kubectl apply -f deployment.yml`**

```
Step 1: Kubernetes reads the file
  ↓
Step 2: Validates the YAML structure
  ↓
Step 3: Checks if Deployment exists
  ↓ (If new)
Step 4: Creates Deployment object
  ↓
Step 5: Deployment controller sees new Deployment
  ↓
Step 6: Reads spec.replicas = 1
  ↓
Step 7: Creates 1 Pod using template
  ↓
Step 8: Pod scheduler finds node with enough resources
  ↓
Step 9: Kubelet on that node pulls image from Docker Hub
  ↓
Step 10: Container runtime starts the container
  ↓
Step 11: Flask app starts inside container
  ↓
Step 12: After 5s, readiness probe checks /health
  ↓ (If healthy)
Step 13: Pod marked as Ready
  ↓
Step 14: Service starts routing traffic to pod
  ✅ DONE!
```

---

## Relationship with Other Resources

### **Deployment + Service**
```yaml
# Deployment creates pods with label
template:
  metadata:
    labels:
      app: flask-app

# Service finds those pods
---
apiVersion: v1
kind: Service
metadata:
  name: flask-service
spec:
  selector:
    app: flask-app  # Finds pods with this label
  ports:
  - port: 80
    targetPort: 8080
```

### **Deployment + KEDA ScaledObject**
```yaml
# KEDA scales this Deployment
---
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: my-scaler
spec:
  scaleTargetRef:
    name: sample-flask-app  # Targets this Deployment
    kind: Deployment
  minReplicaCount: 1
  maxReplicaCount: 10
```

KEDA will modify `spec.replicas` based on your autoscaler's predictions.

---

## Testing Your Deployment

### **1. Apply the file**
```bash
kubectl apply -f demo-app-deployment.yml
```

### **2. Watch pod creation**
```bash
kubectl get pods -n springboot-test -w
```

### **3. Check deployment status**
```bash
kubectl get deployment sample-flask-app -n springboot-test

# Output:
# NAME               READY   UP-TO-DATE   AVAILABLE   AGE
# sample-flask-app   1/1     1            1           30s
```

**What each column means:**
- `READY`: 1/1 = 1 out of 1 pods are ready
- `UP-TO-DATE`: Pods running latest template version
- `AVAILABLE`: Pods ready to serve traffic
- `AGE`: Time since creation

### **4. Check pod details**
```bash
kubectl describe deployment sample-flask-app -n springboot-test
```

### **5. View events**
```bash
kubectl get events -n springboot-test --sort-by='.lastTimestamp'
```

---

## Summary: Essential Fields Meaning

| Field | What It Is | Why It Matters |
|-------|-----------|----------------|
| `apiVersion` | Which API to use | Compatibility with cluster |
| `kind` | Resource type | What you're creating |
| `metadata.name` | Deployment name | How to reference it |
| `spec.replicas` | Number of pods | How many copies run |
| `spec.selector` | How to find pods | Links Deployment to Pods |
| `spec.template` | Pod blueprint | What each pod looks like |
| `containers[].name` | Container name | For logging/debugging |
| `containers[].image` | Docker image | What code to run |
| `containers[].ports` | Exposed ports | How to reach the app |

**Remember:** The selector labels MUST match the template labels, or the Deployment won't work!

That's everything you need to understand Kubernetes Deployments! 🎯
