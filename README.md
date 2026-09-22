# Dockerized 2-Tier Web Application on AWS EC2

![Project Status](https://img.shields.io/badge/Status-Production--Ready-brightgreen)
![Docker](https://img.shields.io/badge/Docker-29.8%2B-blue)
![Docker Compose](https://img.shields.io/badge/Docker%20Compose-v2.x-blue)
![Python](https://img.shields.io/badge/Python-3.11-yellow)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange)
![Nginx](https://img.shields.io/badge/Nginx-Alpine-green)
![AWS](https://img.shields.io/badge/AWS-EC2-orange)

A production-style, beginner-friendly 2-tier Task Manager web application engineered with containerization best practices, microservice isolation, and automated deployment pipelines. Built with HTML/CSS/JavaScript, Python Flask REST API, MySQL 8.0, and Nginx, fully orchestrated via Docker Compose and ready for AWS EC2 cloud deployment.

---

## 📋 Table of Contents
- [Architecture Overview](#-architecture-overview)
- [What This Project Demonstrates](#-what-this-project-demonstrates)
- [Technologies Used](#-technologies-used)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Local Setup & Getting Started](#-local-setup--getting-started)
- [Useful Docker Commands](#-useful-docker-commands)
- [API Endpoints Documentation](#-api-endpoints-documentation)
- [AWS EC2 Deployment Overview](#-aws-ec2-deployment-overview)
- [Screenshots](#-screenshots)
- [Future Improvements](#-future-improvements)
- [Author & License](#-author--license)

---

## 🏗️ Architecture Overview

The application follows a standard **2-Tier Microservice Architecture** separated into presentation, application logic, and database tiers connected over a isolated Docker bridge network.

```text
+-----------------------------------------------------------------------------+
|                               USER BROWSER                                  |
+-----------------------------------------------------------------------------+
                                       |
                                       | HTTP Requests (Port 80)
                                       v
+-----------------------------------------------------------------------------+
| FRONTEND CONTAINER (Nginx)                                                  |
| - Serves static Web UI (index.html, style.css, script.js)                  |
| - Reverse-proxies /api/ requests to backend container                      |
+-----------------------------------------------------------------------------+
                                       |
                                       | Internal Network: app-network (Port 5000)
                                       v
+-----------------------------------------------------------------------------+
| BACKEND CONTAINER (Flask REST API + Gunicorn)                               |
| - Handles business logic, input validation & JSON formatting                |
| - Manages DB connections with exponential backoff retries                   |
+-----------------------------------------------------------------------------+
                                       |
                                       | Internal Network: app-network (Port 3306)
                                       v
+-----------------------------------------------------------------------------+
| DATABASE CONTAINER (MySQL 8.0)                                             |
| - Stores task entities & relational data                                   |
| - Persists data across container restarts using Docker Volume               |
+-----------------------------------------------------------------------------+
                                       |
                                       v
                             [ Named Docker Volume ]
                                (mysql_data)
```

### Key Architectural Highlights
1. **Nginx Reverse Proxying**: The frontend container uses Nginx to serve UI files and proxy `/api/` calls internally to `http://backend:5000/api/`. This completely eliminates **CORS** issues and exposes only a single secure HTTP port (80).
2. **Container Isolation & Security**: Database port 3306 and Backend port 5000 are **NOT** exposed to the host machine or public internet. Communication happens exclusively within the isolated Docker bridge network (`app-network`).
3. **Database Auto-Healing & Initialization**: The Flask backend includes built-in retry logic that waits for MySQL container readiness before launching, automatically running schema initializations if tables are missing.
4. **Data Persistence**: Database files are stored in a managed Docker volume (`mysql_data`), preserving data even if containers are stopped or recreated.

---

## 🎓 What This Project Demonstrates

This project is tailored for DevOps engineers, cloud developers, and system administrators to demonstrate practical hands-on proficiency in core concepts:

- **Docker Containerization**: Packaging frontend, API, and database into lightweight, predictable container images using custom `Dockerfile` specifications and Alpine/Slim base images.
- **Multi-Container Orchestration (Docker Compose)**: Managing container lifecycles, service dependencies (`depends_on`), healthchecks, port mappings, and volume mounts in `docker-compose.yml`.
- **Custom Container Networking**: Configuring custom Docker bridge networks so microservices communicate seamlessly using internal container names (`db`, `backend`) rather than `localhost`.
- **Dynamic Configuration via Environment Variables**: Externalizing database credentials and port configurations using `.env` files and Docker Compose environment injection.
- **Persistent Docker Volumes**: Preventing data loss by mounting named volumes to persist database records independently of container lifecycles.
- **Production REST API Design**: Implementing CRUD endpoints with Python Flask, PyMySQL connection pooling, status codes, and JSON response contracts.
- **Nginx Web Server & Reverse Proxy**: Configuring Nginx location blocks for static asset delivery and backend reverse proxying.
- **AWS EC2 Cloud Deployment**: Deploying containerized stacks on Ubuntu EC2 instances, configuring AWS Security Groups, and managing cloud firewall rules.
- **Logging & System Troubleshooting**: Inspecting container logs, monitoring real-time output, and diagnosing multi-tier application failures.

---

## 🛠️ Technologies Used

- **Frontend**: HTML5, Modern CSS3 (Vanilla Glassmorphism), ES6 JavaScript (`fetch` API).
- **Web Server / Reverse Proxy**: Nginx (Alpine Linux).
- **Backend API**: Python 3.11, Flask, Gunicorn, PyMySQL.
- **Database**: MySQL 8.0.
- **Containerization**: Docker, Docker Compose (v2+).
- **Cloud Infrastructure**: AWS EC2 (Ubuntu 22.04 LTS / 24.04 LTS).

---

## 📁 Project Structure

```text
docker-2tier-task-manager/
├── backend/
│   ├── app.py              # Flask API application with MySQL retry logic & CRUD endpoints
│   ├── requirements.txt    # Python dependencies (Flask, PyMySQL, Gunicorn, etc.)
│   └── Dockerfile          # Production multi-stage Dockerfile (Python 3.11 slim)
│
├── frontend/
│   ├── index.html          # Task Manager web application HTML layout
│   ├── style.css           # Glassmorphism dark mode CSS design system
│   ├── script.js           # Vanilla JS fetch logic & UI state manager
│   ├── nginx.conf          # Nginx web server & API reverse proxy configuration
│   └── Dockerfile          # Nginx Alpine Dockerfile
│
├── mysql/
│   └── init.sql            # Database schema & starter demo data initialization
│
├── .env.example            # Environment variables template for configuration
├── .dockerignore           # Excluded files for Docker build context
├── .gitignore              # Excluded files for Git control (protecting secrets)
├── docker-compose.yml      # Multi-container orchestration specification
├── DEPLOYMENT.md           # AWS EC2 cloud deployment step-by-step guide
└── README.md               # Project documentation & interview guide
```

---

## ⚡ Prerequisites

Before running this project locally or on AWS, ensure you have installed:

1. **Docker Desktop** (Windows / macOS) or **Docker Engine** (Linux) `v20.10+`
2. **Docker Compose** `v2.0+`
3. **Git** `v2.x+`

Verify your installation:
```bash
docker --version
docker compose version
git --version
```

---

## 🚀 Local Setup & Getting Started

Follow these steps to run the complete 2-tier application locally in less than 2 minutes.

### Step 1: Clone the Repository
```bash
git clone https://github.com/your-username/docker-2tier-task-manager.git
cd docker-2tier-task-manager
```

### Step 2: Create Environment Configuration
Copy the `.env.example` file to create your local `.env` file:
```bash
cp .env.example .env
```

*(Optional)* Customize database credentials in `.env` if desired:
```env
MYSQL_ROOT_PASSWORD=rootpassword123
MYSQL_DATABASE=taskdb
MYSQL_USER=taskuser
MYSQL_PASSWORD=taskpassword123
MYSQL_HOST=db
MYSQL_PORT=3306
PORT=5000
```

### Step 3: Build and Start Containers
Run Docker Compose to build images, create networks, attach volumes, and start all containers in detached mode:
```bash
docker compose up -d --build
```

### Step 4: Verify Container Status
Check that all 3 services (`task-db`, `task-backend`, `task-frontend`) are running:
```bash
docker compose ps
```

*Expected Output:*
```text
NAME            IMAGE                              COMMAND                  SERVICE    CREATED          STATUS                   PORTS
task-db         mysql:8.0                          "docker-entrypoint.s…"   db         10 seconds ago   Up 10 seconds (healthy)  3306/tcp
task-backend    docker-2tier-task-manager-backend  "gunicorn --workers=…"   backend    10 seconds ago   Up 10 seconds            5000/tcp
task-frontend   docker-2tier-task-manager-frontend "nginx -g 'daemon of…"   frontend   10 seconds ago   Up 10 seconds            0.0.0.0:80->80/tcp
```

### Step 5: Access Application
Open your web browser and navigate to:
```text
http://localhost
```

---

## 🛠️ Useful Docker Commands

Here is a quick reference table of essential Docker Compose commands used to operate and troubleshoot this project:

| Command | Purpose & Description |
| :--- | :--- |
| `docker compose up -d --build` | Builds container images from scratch and starts all services in the background (detached mode). |
| `docker compose ps` | Lists all active containers managed by Compose along with their current health and port mappings. |
| `docker compose logs` | Displays combined log output from all running containers. |
| `docker compose logs -f backend` | Streams live tail logs from the backend Flask API container for debugging. |
| `docker compose logs -f db` | Streams live tail logs from the MySQL database container. |
| `docker compose exec backend bash` | Opens an interactive bash terminal shell inside the running backend container. |
| `docker compose exec db mysql -u taskuser -p` | Connects directly to the MySQL database inside the container. |
| `docker compose stop` | Gracefully stops running containers without removing them or deleting data. |
| `docker compose down` | Stops and removes all containers, networks, and default artifacts. |
| `docker compose down -v` | Stops containers and **deletes persistent Docker volumes** (`mysql_data`), resetting the database. |

---

## 📡 API Endpoints Documentation

The backend Flask API serves JSON responses over RESTful endpoints.

| Method | Endpoint | Description | Request Body Example | Success Status |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | Service health check | N/A | `200 OK` |
| `GET` | `/api/tasks` | Fetch all tasks | N/A | `200 OK` |
| `POST` | `/api/tasks` | Create a new task | `{"title": "Setup EC2", "description": "Configure SG"}` | `201 Created` |
| `PUT` | `/api/tasks/<id>` | Update task status or content | `{"status": "completed"}` | `200 OK` |
| `DELETE` | `/api/tasks/<id>` | Delete task by ID | N/A | `200 OK` |

### Sample API Response (`GET /api/tasks`):
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "title": "Set up Docker Compose",
      "description": "Configure multi-container setup with MySQL, Flask backend, and Nginx frontend.",
      "status": "completed",
      "created_at": "2026-09-22 22:45:00"
    },
    {
      "id": 2,
      "title": "Deploy on AWS EC2",
      "description": "Launch an Ubuntu EC2 instance, configure Security Groups, and deploy containerized app.",
      "status": "pending",
      "created_at": "2026-09-22 22:46:00"
    }
  ]
}
```

---

## ☁️ AWS EC2 Deployment Overview

For detailed, step-by-step instructions on deploying this project to an AWS EC2 Ubuntu instance, refer to the complete deployment guide:

📄 **[Read DEPLOYMENT.md](DEPLOYMENT.md)**

### Security Group Configuration Summary
To protect your cloud infrastructure, only expose necessary ports in your AWS EC2 Security Group:

| Type | Protocol | Port Range | Source | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| SSH | TCP | `22` | My IP (`x.x.x.x/32`) | Secure terminal access to EC2 instance |
| HTTP | TCP | `80` | `0.0.0.0/0` | Public web access to Nginx frontend |
| HTTPS | TCP | `443` | `0.0.0.0/0` | Secure SSL web access (Optional / Production) |

> 🔒 **Security Best Practice**: Keep MySQL Port `3306` and Flask Port `5000` **CLOSED** in the AWS Security Group. They communicate securely inside the internal Docker bridge network!

---

## 📸 Screenshots

*(Add screenshots of your running application and AWS EC2 instance here for your portfolio!)*

```text
+-------------------------------------------------------------------+
|                     [ Web Application Screenshot ]                 |
|                                                                   |
|   Add Task Form                  Task Overview Cards              |
|   - Title Input                  - Total: 3                       |
|   - Description Area             - Pending: 2  Completed: 1      |
+-------------------------------------------------------------------+
```

---

## 🔮 Future Improvements

- [ ] **SSL/TLS Encryption**: Integrate Let's Encrypt / Certbot with Nginx for HTTPS traffic.
- [ ] **CI/CD Pipeline**: Implement GitHub Actions workflow to automate linting, Docker image builds, and automated SSH deployment to EC2 upon code push.
- [ ] **Monitoring & Logging**: Add Prometheus and Grafana container services for real-time memory and CPU metrics.
- [ ] **Managed Database Option**: Transition from containerized MySQL to AWS RDS (Relational Database Service) for multi-AZ high availability.

---

## 👤 Author & License

Developed as a DevOps Portfolio Project.

- **GitHub**: [github.com/your-username](https://github.com/your-username)
- **LinkedIn**: [linkedin.com/in/your-profile](https://linkedin.com/in/your-profile)
- **License**: MIT License
