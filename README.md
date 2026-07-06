# 🤖 AI-Powered Customer Service Intelligence Platform

**A local-first, cloud-ready, microservices-based multi-channel decision support system**

> Full-stack dissertation project featuring chatbot, AI classification, workflow automation, hybrid data storage and interactive analytics.

---

## 🏗️ Architecture

```
Client Layer        → Next.js Web App | React Native Mobile
Gateway Layer       → Nginx (routing, rate limiting, CORS)
Microservices (×10) → Auth | Users | Cases | AI | Chatbot | Automation | Notifications | Analytics | Files | Audit
Data Layer          → PostgreSQL + MongoDB + Local File Storage
Infrastructure      → Docker Compose | MailHog (email) | Redis (caching)
```

---

## 🚀 Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (running)
- Node.js 20+ (for web app development)

### 1. Clone and configure
```bash
git clone <repo>
cd Project
cp .env .env  # Already configured for local development
```

### 2. Train AI Models first (recommended)
```bash
cd services/ai-service
pip install -r requirements.txt
python -m app.ml.train
cd ../..
```

### 3. Start all services
```bash
docker-compose up --build
```

This starts:
- **PostgreSQL** on port 5432
- **MongoDB** on port 27017
- **Redis** on port 6379
- **MailHog** (email UI) on http://localhost:8025
- **All 10 microservices** on ports 8001–8010
- **Nginx** reverse proxy on port 80

### 4. Start the web app (development)
```bash
cd web-app
npm install
npm run dev
```

Open **http://localhost:3000**

---

## 🔑 Default Accounts

| Role       | Email                          | Password    |
|------------|-------------------------------|-------------|
| Admin      | admin@csplatform.local        | Admin@123   |
| Manager    | manager@csplatform.local      | Admin@123   |
| Supervisor | supervisor@csplatform.local   | Admin@123   |
| Agent      | agent1@csplatform.local       | Admin@123   |
| Customer   | customer@csplatform.local     | Admin@123   |

---

## 🛠️ Services

| Service       | Port | Technology | Responsibility                         |
|---------------|------|------------|----------------------------------------|
| Auth          | 8001 | FastAPI    | JWT, RBAC, MFA, token refresh          |
| Users         | 8002 | FastAPI    | CRUD, roles, status management         |
| Cases         | 8003 | FastAPI    | Full case lifecycle + AI integration   |
| AI            | 8004 | FastAPI+ML | Category/Priority/Sentiment + SHAP     |
| Chatbot       | 8005 | FastAPI    | Hybrid NLP chatbot + session management|
| Automation    | 8006 | FastAPI    | 8 rule-based workflow triggers         |
| Notifications | 8007 | FastAPI    | Email (SMTP) + in-app alerts           |
| Analytics     | 8008 | FastAPI    | KPI aggregation + reporting            |
| Files         | 8009 | FastAPI    | Upload, download, validation           |
| Audit         | 8010 | FastAPI    | MongoDB activity logging               |

---

## 🧠 AI Features

- **Category classification** — 9 categories (billing, technical support, account, etc.)
- **Priority prediction** — low / medium / high / urgent
- **Sentiment analysis** — positive / neutral / negative
- **SHAP explainability** — top contributing features per prediction
- **Confidence scores** — per-class probabilities
- **Auto ML trigger** — via Admin → Train Models button

To manually train:
```bash
curl -X POST http://localhost:8004/ai/train
```
Or via the Admin panel: http://localhost:3000/dashboard/admin

---

## 🤖 Chatbot

Hybrid architecture:
1. **Rule-based** flow for structured intake
2. **Intent detection** via regex pattern matching (13 intents)
3. **FAQ retrieval** via MongoDB full-text search
4. **Escalation** → automatically creates a support ticket
5. **Session management** → persisted in MongoDB

Test at: http://localhost:3000/dashboard/chatbot

---

## 📊 Analytics

Available dashboards:
- Case volume trend (30 days)
- Sentiment distribution
- Priority breakdown
- Category distribution
- Agent performance table
- SLA compliance rate

---

## 🔧 API Documentation

Auto-generated Swagger UI available at:
- Auth:       http://localhost:8001/docs
- Users:      http://localhost:8002/docs
- Cases:      http://localhost:8003/docs
- AI:         http://localhost:8004/docs
- Chatbot:    http://localhost:8005/docs
- Automation: http://localhost:8006/docs
- Analytics:  http://localhost:8008/docs
- Files:      http://localhost:8009/docs
- Audit:      http://localhost:8010/docs

---

## 🧪 Running Tests

### Backend (Unit & Integration)
Run the complete test suite (240+ tests) across all microservices and cross-service integration tests from the root directory:
```bash
python -m pytest services/ tests/ -v
```
Or test an individual service:
```bash
cd services/auth-service
pytest tests/ -v
```

### Web App (Frontend)
Run the React/Next.js component and API client tests:
```bash
cd web-app
npm test
```

---

## 🐳 Docker Commands

```bash
# Start everything
docker-compose up --build

# Start specific service
docker-compose up auth-service postgres

# View logs
docker-compose logs -f case-service

# Stop all
docker-compose down

# Reset databases (⚠️ destroys data)
docker-compose down -v
```

---

## ☁️ Cloud Deployment Strategy

This system is **architected for cloud deployment** with the following mapping:

| Local Component | Azure Equivalent         | AWS Equivalent        |
|----------------|--------------------------|----------------------|
| PostgreSQL     | Azure Database for PostgreSQL | RDS PostgreSQL  |
| MongoDB        | Azure Cosmos DB          | DocumentDB            |
| File Storage   | Azure Blob Storage       | S3                    |
| Services       | Azure Container Apps     | ECS Fargate           |
| Nginx Gateway  | Azure API Management     | API Gateway           |
| Redis          | Azure Cache for Redis    | ElastiCache           |
| MailHog        | SendGrid / Azure Comm.   | SES                   |

Estimated monthly cost for production (Azure): **£120–250/month** for a small team deployment.

---

## 📁 Project Structure

```
Project/
├── services/
│   ├── auth-service/          # FastAPI — JWT, RBAC, MFA
│   ├── user-service/          # FastAPI — User management
│   ├── case-service/          # FastAPI — Case lifecycle
│   ├── ai-service/            # FastAPI + scikit-learn — ML inference
│   ├── chatbot-service/       # FastAPI + Motor — Hybrid chatbot
│   ├── automation-service/    # FastAPI — Workflow triggers
│   ├── notification-service/  # FastAPI + aiosmtplib — Emails
│   ├── analytics-service/     # FastAPI — KPI queries
│   ├── file-service/          # FastAPI — File handling
│   └── audit-service/         # FastAPI + Motor — Activity logs
├── database/
│   ├── postgres/              # Schema + seed SQL
│   └── mongodb/               # Collections + FAQ seed
├── web-app/                   # Next.js 14 + TypeScript
├── mobile-app/                # React Native (scaffold)
├── nginx/                     # Reverse proxy config
├── ml/                        # Notebooks and model artefacts
├── docs/                      # Architecture and deployment docs
├── docker-compose.yml
└── .env
```

---

## 🔐 Security Features

- JWT access tokens (30 min) + refresh token rotation (7 days)
- bcrypt password hashing
- Role-based access control (5 roles)
- Rate limiting via Nginx
- MIME-type file validation
- Input validation via Pydantic
- Audit trail for all critical actions
- MFA (TOTP) support — designed for Microsoft Entra integration
- Session expiry and token revocation

---

## 📜 License

Built for academic dissertation purposes.
