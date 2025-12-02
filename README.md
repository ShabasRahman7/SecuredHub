# SecuredHub

SecuredHub is a multi-tenant DevSecOps platform designed to integrate security scanning directly into your development workflow. It provides organizations with a centralized dashboard to manage repositories, monitor vulnerabilities, and automate security checks.

## Key Features

- **Multi-Tenancy**: Isolated workspaces for different organizations and teams.
- **Repository Management**: Securely connect and manage private and public repositories.
- **Automated Scanning**: Scheduled and trigger-based security scans for codebases.
- **Vulnerability Tracking**: Real-time dashboard for tracking and analyzing security issues.
- **Role-Based Access**: Granular permissions for Owners, Developers, and Viewers.

## Tech Stack

- **Backend**: Django REST Framework (Python), Celery, Redis
- **Frontend**: React (Vite), TailwindCSS, DaisyUI
- **Infrastructure**: Docker, Nginx, PostgreSQL

## getting Started

### Prerequisites

- Docker & Docker Compose
- Node.js (v18+)

### Installation

1. Can clone the repository:
   ```bash
   git clone https://github.com/ShabasRahman7/SecuredHub.git
   ```

2. Start the application services:
   ```bash
   docker-compose up -d --build
   ```

3. Run the frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

The application will be available at `http://localhost:5173`.
