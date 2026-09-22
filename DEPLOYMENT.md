# AWS EC2 Deployment Guide: Dockerized 2-Tier Task Manager

This deployment guide provides complete, step-by-step instructions for deploying the **Dockerized 2-Tier Task Manager** application on an AWS EC2 instance running Ubuntu Linux (22.04 LTS or 24.04 LTS).

---

## 📋 Table of Contents
- [Prerequisites](#-prerequisites)
- [Step 1: Launch an AWS EC2 Instance](#step-1-launch-an-aws-ec2-instance)
- [Step 2: Configure AWS Security Group Rules](#step-2-configure-aws-security-group-rules)
- [Step 3: Connect to EC2 via SSH](#step-3-connect-to-ec2-via-ssh)
- [Step 4: Update System & Install Docker](#step-4-update-system--install-docker)
- [Step 5: Verify Docker & Docker Compose Installation](#step-5-verify-docker--docker-compose-installation)
- [Step 6: Clone GitHub Repository](#step-6-clone-github-repository)
- [Step 7: Configure Environment Variables](#step-7-configure-environment-variables)
- [Step 8: Build and Start Containers](#step-8-build-and-start-containers)
- [Step 9: Verify Running Containers & Logs](#step-9-verify-running-containers--logs)
- [Step 10: Access Application via Public IP](#step-10-access-application-via-public-ip)
- [Step 11: Container Lifecycle Management](#step-11-container-lifecycle-management)
- [Step 12: Troubleshooting Guide](#step-12-troubleshooting-guide)

---

## ⚡ Prerequisites

Before starting, ensure you have:
1. An active **AWS Account**.
2. An SSH Key Pair (`.pem` file) created in your AWS region.
3. Git repository URL for your project.

---

## Step 1: Launch an AWS EC2 Instance

1. Log in to the [AWS Management Console](https://console.aws.amazon.com/) and navigate to **EC2 Dashboard**.
2. Click **Launch Instance**.
3. **Name**: `task-manager-ec2`
4. **AMI (Amazon Machine Image)**: Select **Ubuntu Server 24.04 LTS** or **22.04 LTS (64-bit x86)**.
5. **Instance Type**: Select `t2.micro` or `t3.micro` (Free Tier eligible).
6. **Key Pair**: Select an existing key pair or click *Create new key pair* (RSA, `.pem` format) and download `your-key.pem` to your local machine.
7. **Network Settings**: Proceed to Step 2 for Security Group configuration.

---

## Step 2: Configure AWS Security Group Rules

The Security Group acts as a virtual firewall for your EC2 instance. **Only open ports that are strictly necessary.**

### Inbound Rules Configuration:

| Type | Protocol | Port Range | Source | Rationale / Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **SSH** | TCP | `22` | `My IP` (`x.x.x.x/32`) | Allows secure command line access to your server. |
| **HTTP** | TCP | `80` | `0.0.0.0/0` | Allows public web traffic to reach Nginx frontend. |
| **HTTPS** | TCP | `443` | `0.0.0.0/0` | Allows encrypted SSL web traffic (Optional / Production). |

> 🔒 **Security Warning**:
> - **Do NOT** open Port `3306` (MySQL) or Port `5000` (Flask API) to the internet (`0.0.0.0/0`).
> - The Flask API and MySQL database communicate internally inside the isolated Docker network (`app-network`). Exposing them publicly exposes your system to unauthorized database access and security threats!

---

## Step 3: Connect to EC2 via SSH

1. Open your terminal (Linux/macOS) or PowerShell (Windows).
2. Set permissions for your downloaded `.pem` key file (Linux/macOS only):
   ```bash
   chmod 400 your-key.pem
   ```
3. Connect to your EC2 instance using its **Public IPv4 Address**:
   ```bash
   ssh -i /path/to/your-key.pem ubuntu@<YOUR_EC2_PUBLIC_IP>
   ```
   *Example:*
   ```bash
   ssh -i ~/.ssh/my-aws-key.pem ubuntu@54.210.45.12
   ```

---

## Step 4: Update System & Install Docker

Once logged into your EC2 Ubuntu instance, run the official Docker installation commands:

```bash
# 1. Update package index and install prerequisites
sudo apt update && sudo apt upgrade -y
sudo apt install -y ca-certificates curl gnupg lsb-release

# 2. Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 3. Set up the Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 4. Install Docker Engine, CLI, and Docker Compose plugin
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 5. Add current user (ubuntu) to docker group to execute docker without 'sudo'
sudo usermod -aG docker $USER
```

> ⚠️ **Important**: Log out and reconnect via SSH so group membership updates take effect:
```bash
exit
ssh -i /path/to/your-key.pem ubuntu@<YOUR_EC2_PUBLIC_IP>
```

---

## Step 5: Verify Docker & Docker Compose Installation

Check that Docker Engine and Docker Compose are active and running:

```bash
docker --version
docker compose version
```

*Expected Output:*
```text
Docker version 27.x.x, build ...
Docker Compose version v2.x.x
```

---

## Step 6: Clone GitHub Repository

Clone your project repository onto the EC2 server:

```bash
git clone https://github.com/your-username/docker-2tier-task-manager.git
cd docker-2tier-task-manager
```

---

## Step 7: Configure Environment Variables

Create the `.env` production configuration file from `.env.example`:

```bash
cp .env.example .env
```

Edit `.env` to set secure credentials using `nano` or `vim`:
```bash
nano .env
```

Update values:
```env
MYSQL_ROOT_PASSWORD=SecureRootPass2026!
MYSQL_DATABASE=taskdb
MYSQL_USER=taskuser
MYSQL_PASSWORD=SecureUserPass2026!
MYSQL_HOST=db
MYSQL_PORT=3306
PORT=5000
FLASK_ENV=production
```
Press `Ctrl + O` then `Enter` to save, and `Ctrl + X` to exit `nano`.

---

## Step 8: Build and Start Containers

Launch the multi-container stack in detached mode:

```bash
docker compose up -d --build
```

Docker Compose will perform the following automatically:
1. Pull the official `mysql:8.0` and `nginx:alpine` images.
2. Build the Flask backend container image from `./backend/Dockerfile`.
3. Build the Nginx frontend container image from `./frontend/Dockerfile`.
4. Create the custom bridge network (`app-network`).
5. Create persistent volume (`mysql_data`).
6. Initialize MySQL database with `./mysql/init.sql`.
7. Boot up containers in sequence (`db` -> `backend` -> `frontend`).

---

## Step 9: Verify Running Containers & Logs

### 1. Verify Active Containers
```bash
docker compose ps
```
Ensure all 3 services display status `Up` or `Up (healthy)`.

### 2. Check Service Logs
```bash
# View all container logs
docker compose logs

# View live backend API logs
docker compose logs -f backend

# View live MySQL database logs
docker compose logs -f db
```

---

## Step 10: Access Application via Public IP

Open your web browser and navigate to your EC2 instance's Public IPv4 address:

```text
http://<YOUR_EC2_PUBLIC_IP>
```

*Example:* `http://54.210.45.12`

Test the Task Manager application:
1. View initial seeded tasks loaded from MySQL database.
2. Add a new task (e.g. "Configure CloudWatch Alarms").
3. Click **Complete** to toggle task status.
4. Click **Delete** to remove a task.

---

## Step 11: Container Lifecycle Management

### Stop Containers (Preserving Data)
To temporarily halt application services:
```bash
docker compose stop
```

### Restart Containers
To restart stopped services:
```bash
docker compose start
```

### Rebuild After Code Changes
If you update code or configuration:
```bash
docker compose up -d --build
```

### Complete Teardown (Preserving Data)
Stops containers and removes Docker networks:
```bash
docker compose down
```

### Total Teardown (Deleting Database Data)
Stops containers and **deletes the MySQL persistent volume**:
```bash
docker compose down -v
```

---

## Step 12: Troubleshooting Guide

### Issue 1: Cannot connect to `http://<EC2_PUBLIC_IP>` in browser
- **Cause**: Security Group rule missing or incorrect.
- **Fix**: Verify Inbound Rule in AWS EC2 Security Group for **HTTP Port 80** with source `0.0.0.0/0`.

### Issue 2: Backend cannot connect to MySQL ("Connection Refused")
- **Cause**: MySQL container is still initializing.
- **Fix**: The backend automatically retries 10 times. Inspect logs with `docker compose logs -f backend`. Verify `MYSQL_HOST=db` in `.env`.

### Issue 3: `Permission denied` when running Docker commands
- **Cause**: User not added to `docker` group.
- **Fix**: Run `sudo usermod -aG docker $USER` and log out/in via SSH.

### Issue 4: Port 80 already in use
- **Cause**: Another web server (e.g. standalone Nginx or Apache) is running on the host.
- **Fix**: Stop the host web server using `sudo systemctl stop nginx` or change host port in `docker-compose.yml` (`8080:80`).
