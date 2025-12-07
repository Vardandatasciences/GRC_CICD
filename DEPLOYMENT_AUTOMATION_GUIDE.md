# 🚀 Automated Deployment Guide: Docker + Nginx + GitHub Actions → EC2

## 📋 Overview

This guide explains the automated deployment setup for your Vue.js frontend using:
- **Docker**: Containerizes your application
- **Nginx**: Serves your built frontend files
- **GitHub Actions**: Automates the deployment process
- **Self-hosted Runner**: Runs on your EC2 instance

---

## 📁 Files Created/Modified

### 1. `frontend/Dockerfile`
**What it does:**
- **Multi-stage build** (2 stages):
  - **Stage 1 (build-stage)**: Uses Node.js to build your Vue.js app
    - Installs dependencies
    - Runs `npm run build` to create production files in `dist/`
  - **Stage 2 (production-stage)**: Uses lightweight Nginx Alpine image
    - Copies your built files from Stage 1
    - Uses your custom `nginx-complete.conf` configuration
    - Serves the app on port 80

**Why multi-stage?**
- Final image is smaller (only Nginx, not Node.js)
- Faster deployments
- More secure (no build tools in production)

### 2. `frontend/.dockerignore`
**What it does:**
- Tells Docker which files to **exclude** when building
- Reduces build context size
- Speeds up builds

### 3. `.github/workflows/main.yml`
**What it does:**
- **Triggers**: Runs when you push to `main` branch (or manually)
- **Steps**:
  1. Checks out your code
  2. Builds Docker image
  3. Stops old container
  4. Runs new container
  5. Health checks
  6. Cleans up old images

### 4. `frontend/docker-compose.yml` (Optional)
**What it does:**
- Alternative way to run Docker containers
- Useful for local testing or manual deployments

---

## 🔧 Setup Instructions

### Step 1: Set Up Self-Hosted Runner on EC2

1. **SSH into your EC2 instance:**
   ```bash
   ssh -i your-key.pem ec2-user@your-ec2-ip
   ```

2. **Install Docker (if not already installed):**
   ```bash
   # For Amazon Linux 2
   sudo yum update -y
   sudo yum install docker -y
   sudo systemctl start docker
   sudo systemctl enable docker
   sudo usermod -aG docker ec2-user
   
   # Log out and back in for group changes to take effect
   ```

3. **Install GitHub Actions Runner:**
   ```bash
   # Create a folder
   mkdir actions-runner && cd actions-runner
   
   # Download the latest runner package
   curl -o actions-runner-linux-x64-2.311.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz
   
   # Extract the installer
   tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz
   ```

4. **Configure the runner:**
   - Go to your GitHub repository
   - Settings → Actions → Runners → New self-hosted runner
   - Copy the configuration command (looks like: `./config.sh --url https://github.com/... --token ...`)
   - Run it on your EC2 instance

5. **Start the runner:**
   ```bash
   ./run.sh
   ```
   
   **To run as a service (recommended):**
   ```bash
   sudo ./svc.sh install
   sudo ./svc.sh start
   ```

### Step 2: Verify Docker Setup

```bash
# Test Docker
docker --version
docker ps

# Test building your image locally (optional)
cd /path/to/frontend
docker build -t frontend-grc:test .
docker run -d -p 8080:80 --name test-container frontend-grc:test
curl http://localhost:8080
docker stop test-container && docker rm test-container
```

### Step 3: Push Your Code

```bash
git add .
git commit -m "Add automated deployment setup"
git push origin main
```

The workflow will automatically trigger!

---

## 🔄 How the Deployment Flow Works

```
┌─────────────────┐
│  You push code  │
│  to GitHub      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ GitHub Actions  │
│ detects push    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Self-hosted     │
│ Runner starts   │
│ workflow        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 1. Checkout     │
│    code         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. Build Docker │
│    image        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. Stop old     │
│    container    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. Run new      │
│    container    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 5. Health check │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ✅ Deployed!    │
└─────────────────┘
```

---

## 📝 Understanding the Workflow File

### Triggers
```yaml
on:
  push:
    branches:
      - main
    paths:
      - 'frontend/**'  # Only runs when frontend changes
```
- Runs on push to `main` branch
- Only when files in `frontend/` change (saves resources)

### Runner
```yaml
runs-on: self-hosted
```
- Uses your EC2 instance as the runner
- No GitHub-hosted runner minutes used!

### Build Step
```yaml
docker build -t frontend-grc:latest .
```
- Builds image with tag `latest`
- Also tags with commit SHA for versioning

### Container Management
```yaml
docker stop ${{ env.DOCKER_CONTAINER_NAME }}
docker rm ${{ env.DOCKER_CONTAINER_NAME }}
docker run -d --name ... --restart unless-stopped ...
```
- Stops old container gracefully
- Removes it
- Starts new one with auto-restart

---

## 🧪 Testing Locally

### Test Docker Build
```bash
cd frontend
docker build -t frontend-grc:test .
docker run -d -p 8080:80 --name test-frontend frontend-grc:test
# Visit http://localhost:8080
docker stop test-frontend && docker rm test-frontend
```

### Test with Docker Compose
```bash
cd frontend
docker-compose up -d
# Visit http://localhost
docker-compose down
```

---

## 🐛 Troubleshooting

### Issue: Workflow doesn't trigger
**Solution:**
- Check if runner is online: GitHub → Settings → Actions → Runners
- Check branch name matches (main vs master)
- Check if files changed are in `frontend/` directory

### Issue: Docker build fails
**Solution:**
```bash
# Check Docker is running
sudo systemctl status docker

# Check disk space
df -h

# Check Docker logs
docker logs frontend-grc-container
```

### Issue: Container won't start
**Solution:**
```bash
# Check if port 80 is already in use
sudo netstat -tulpn | grep :80

# Check container logs
docker logs frontend-grc-container

# Check nginx config
docker exec frontend-grc-container nginx -t
```

### Issue: Runner not picking up jobs
**Solution:**
```bash
# Restart runner service
cd ~/actions-runner
sudo ./svc.sh stop
sudo ./svc.sh start

# Or check runner status
./run.sh  # Run in foreground to see errors
```

---

## 🔐 Security Best Practices

1. **Don't commit secrets**: Use GitHub Secrets for sensitive data
2. **Use specific image tags**: Tag with commit SHA for traceability
3. **Keep images updated**: Regularly update base images (nginx:alpine, node:18-alpine)
4. **Limit port exposure**: Only expose necessary ports
5. **Use non-root user**: Consider adding user to Dockerfile (advanced)

---

## 📊 Monitoring

### Check Container Status
```bash
docker ps | grep frontend-grc
docker stats frontend-grc-container
```

### View Logs
```bash
docker logs frontend-grc-container
docker logs -f frontend-grc-container  # Follow logs
```

### Check Nginx Access
```bash
docker exec frontend-grc-container cat /var/log/nginx/access.log
```

---

## 🎯 Next Steps (Optional Enhancements)

1. **Add environment variables**: Use GitHub Secrets
2. **Add rollback mechanism**: Keep previous image version
3. **Add notifications**: Slack/Email on deployment
4. **Add staging environment**: Deploy to different port
5. **Add health checks**: Automated testing after deployment
6. **Add database migrations**: If you have backend too

---

## 📚 Key Concepts Explained

### Docker
- **Container**: Lightweight, isolated environment
- **Image**: Blueprint for containers
- **Dockerfile**: Instructions to build an image

### Nginx
- **Web server**: Serves static files (your built Vue app)
- **Reverse proxy**: Can forward API requests to backend
- **SPA routing**: `try_files` directive handles Vue Router

### GitHub Actions
- **Workflow**: Automated process (your YAML file)
- **Runner**: Machine that executes workflows
- **Self-hosted**: Your own machine (EC2) instead of GitHub's

### Multi-stage Build
- **Stage 1**: Build environment (Node.js, npm, etc.)
- **Stage 2**: Production environment (only Nginx)
- **Result**: Smaller, faster, more secure final image

---

## ✅ Checklist

- [ ] Docker installed on EC2
- [ ] Self-hosted runner configured and running
- [ ] Dockerfile created in frontend/
- [ ] Workflow file created in .github/workflows/
- [ ] Pushed code to trigger workflow
- [ ] Verified deployment works
- [ ] Container accessible on port 80

---

## 🎉 You're All Set!

Every time you push to `main`, your frontend will automatically:
1. Build into a Docker image
2. Deploy to your EC2 instance
3. Serve via Nginx

No manual steps needed! 🚀

