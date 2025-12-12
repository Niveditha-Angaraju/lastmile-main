# Kubernetes Cluster Setup

## Problem: Cluster Not Running

If you see this error:
```
Unable to connect to the server: dial tcp 192.168.49.2:8443: connect: no route to host
```

Your Kubernetes cluster (Minikube) is **stopped** and needs to be started.

## Quick Fix

### Start Minikube

```bash
minikube start
```

This will:
- Start the Minikube VM
- Initialize the Kubernetes cluster
- Configure kubectl to connect to it

### Verify Cluster is Running

```bash
# Check Minikube status
minikube status

# Should show:
# type: Control Plane
# host: Running
# kubelet: Running
# apiserver: Running

# Check Kubernetes connectivity
kubectl cluster-info

# Check nodes
kubectl get nodes
```

## Complete Setup

### 1. Start Minikube

```bash
# Start Minikube
minikube start

# If you need more resources:
minikube start --memory=4096 --cpus=2
```

### 2. Verify Cluster

```bash
# Check status
minikube status

# Test connectivity
kubectl get nodes
kubectl get namespaces
```

### 3. Deploy LastMile Services

```bash
cd /home/niveditha/lastmile-main

# Deploy all services
./infra/scripts/deploy_lastmile.sh

# Or manually:
kubectl apply -f infra/k8s/namespace.yaml
kubectl apply -f infra/k8s/postgres-statefulset.yaml
kubectl apply -f infra/k8s/rabbitmq-deployment.yaml
# ... etc
```

### 4. Verify Services Running

```bash
# Check all pods
kubectl -n lastmile get pods

# All should be "Running" or "Ready"
```

## Troubleshooting

### Minikube Won't Start

**Error: "driver not found"**
```bash
# Install a driver (choose one):
# Docker (if Docker is installed)
minikube start --driver=docker

# Or VirtualBox
minikube start --driver=virtualbox

# Or KVM2
minikube start --driver=kvm2
```

**Error: "insufficient memory"**
```bash
# Start with less resources
minikube start --memory=2048 --cpus=2
```

**Error: "VM not found"**
```bash
# Delete and recreate
minikube delete
minikube start
```

### kubectl Can't Connect

**Check kubeconfig:**
```bash
# View current context
kubectl config current-context

# Should show: minikube

# If not, set it:
kubectl config use-context minikube
```

**Reset kubeconfig:**
```bash
minikube stop
minikube start
```

### Services Not Deployed

**Check if namespace exists:**
```bash
kubectl get namespace lastmile

# If not, create it:
kubectl create namespace lastmile
```

**Redeploy services:**
```bash
cd /home/niveditha/lastmile-main
./infra/scripts/deploy_lastmile.sh
```

## Daily Usage

### Start Cluster (Morning)

```bash
minikube start
```

### Stop Cluster (Evening - Optional)

```bash
minikube stop
```

### Delete Cluster (Clean Slate)

```bash
minikube delete
minikube start
```

## Alternative: Use Existing Cluster

If you have a different Kubernetes cluster (not Minikube):

```bash
# Check current context
kubectl config current-context

# List all contexts
kubectl config get-contexts

# Switch context
kubectl config use-context <context-name>

# Verify
kubectl cluster-info
kubectl get nodes
```

## Quick Reference

```bash
# Start cluster
minikube start

# Check status
minikube status

# Stop cluster
minikube stop

# Delete cluster
minikube delete

# View dashboard
minikube dashboard

# Get cluster IP
minikube ip

# SSH into cluster
minikube ssh
```

## After Starting Minikube

Once Minikube is running:

1. **Deploy services** (if not already deployed):
   ```bash
   ./infra/scripts/deploy_lastmile.sh
   ```

2. **Run your build script**:
   ```bash
   ./QUICK_BUILD_DEPLOY.sh 1.1 saniyaismail999
   ```

3. **Verify deployment**:
   ```bash
   kubectl -n lastmile get pods
   ```

## Summary

**The error means Minikube is stopped.**

**Fix:**
```bash
minikube start
```

**Then retry:**
```bash
./QUICK_BUILD_DEPLOY.sh 1.1 saniyaismail999
```

The script now checks for cluster connectivity before attempting deployment!

