# 🤖 Clarix: AI-Powered Customer Service Intelligence Platform

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
git clone https://github.com/rafiuzzamans/clarix.git
cd clarix
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
- **MongoDB** on host port 27018 (container port 27017)
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

> ⚠️ Demo accounts for local development only. Change these credentials before any public deployment.

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

- **Category classification** — 6 financial categories mapped from CFPB (debt collection, mortgage, credit reporting, bank account, credit card, student loan)
- **Priority prediction** — high / medium / low based on intake urgency and complexity
- **Sentiment analysis** — positive / neutral / negative financial sentiment
- **SHAP explainability** — deterministic feature attributions per prediction via `shap.LinearExplainer`
- **Confidence scores** — calibrated per-class probabilities
- **Auto ML trigger** — via Admin → Train Models button

To manually train the production pipeline:
```bash
curl -X POST http://localhost:8004/ai/train
```
Or via the Admin panel: http://localhost:3000/dashboard/admin

---

## ⚖️ Routing & Automatic Resolution

**Routing is by category; priority only sets the SLA deadline** (`case-service/app/services/case_service.py`):

| Category | Team |
|---|---|
| `debt_collection`, `credit_card` | Billing Team |
| `mortgage`, `bank_account` | Tier 2 Support |
| `credit_reporting`, `student_loan` | Tier 1 Support |

**Automatic resolution (no human in the loop).** When the category model's confidence is **> 0.85**, the case is assigned to the AI agent. A background worker (`automation-service/app/workers/ai_agent.py`) polls every 10 seconds and, for each case assigned to the AI agent, it:
1. calls `/ai/predict` and writes a customer-visible note (category, confidence, top-3 SHAP terms),
2. marks the case `resolved` and adds a timeline event,
3. writes a `case_resolved_by_ai` entry to the audit log.

On the held-out v2 test set (12,256 complaints), 66.2% of cases score above 0.85 and 96.8% of those are classified correctly (one-off measurement, not yet a saved script).

> **Known limitation:** these are solely automated decisions. There is currently no customer-facing way to contest the outcome or request human review (relevant to GDPR Art. 22). Corrections made by agents are recorded in the timeline and audit log. The `ai_overridden` column exists in the schema but the update path does not set it yet.

The worker reads `DATABASE_URL` from the environment. `docker-compose.yml` builds it from `POSTGRES_USER`, `POSTGRES_PASSWORD` and `POSTGRES_DB` in `.env`; there is no hard-coded default.

---

## 🔬 Empirical Evaluation & Benchmarks (v2)

To ensure academic rigor and reproducibility, CLARIX includes an automated empirical evaluation suite (`ml/scripts/rerun_experiments.py` & `ml/scripts/benchmark_shap_latency.py`).

### Scientific Evaluation Protocol
1. **Deduplication**: Strict deduplication on `complaint_id` and normalized narrative text prior to dataset splitting.
2. **Leakage Prevention**: Priority labels are generated strictly at intake using whole-word regex patterns (`\b...\b`) and text length without utilizing post-resolution signals (`timely_response`).
3. **Natural Test Distribution**: Stratified 80/20 train/test split performed *before* balancing; minority upsampling and majority capping are applied strictly to the training fold.
4. **Fair Model Tuning**: All candidate models share identical TF-IDF vectorization (15,000 max features, unigrams + bigrams, sublinear TF) and 5-fold stratified cross-validation on the training set.

### Model Performance Comparison (Natural Test Set)

| Task | Logistic Regression (Production) | LinearSVC | Random Forest | Multinomial Naive Bayes |
| :--- | :---: | :---: | :---: | :---: |
| **Category (Weighted F1)** | **0.8853** (Macro: 0.8739) | **0.8874** (Macro: 0.8764) | 0.8620 (Macro: 0.8473) | 0.8527 (Macro: 0.8392) |
| **Priority (Weighted F1)** | **0.9163** (Macro: 0.8885) | **0.9177** (Macro: 0.8871) | 0.9025 (Macro: 0.8763) | 0.6822 (Macro: 0.6434) |
| **Sentiment (Weighted F1)** | **0.7414** (Macro: 0.6859) | **0.7445** (Macro: 0.6810) | 0.7269 (Macro: 0.6499) | 0.7176 (Macro: 0.6476) |

### SHAP Latency & Throughput Benchmark

*In-process latency measured over 200 real complaint requests (excluding warmup):*
- **Prediction Only**: 2.0 ms mean (p50: 1.8 ms, p95: 3.6 ms)
- **Prediction + Linear SHAP (Reused Explainer)**: **4.3 ms mean** (p50: 3.8 ms, p95: 8.0 ms)
- **Throughput**: 271.0 req/s (1 worker), 196.7 req/s (5 workers), 169.0 req/s (10 workers)
- **Baseline Invariance**: 86.5% mean Jaccard overlap of top-10 features and 86.7% identical top-1 feature between empty-document (zero) background and training-mean background.

To re-run the benchmark suite:
```bash
python ml/scripts/rerun_experiments.py
python ml/scripts/benchmark_shap_latency.py
```
Reports and artifacts are persisted to `ml/models_v2/evaluation_report_v2.json` and `ml/models_v2/benchmark_report.json`.

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
Run the complete suite (213 service tests + 37 cross-service integration tests; 249 passed, 1 skipped) from the root directory:
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

Released under the MIT License. See [LICENSE](LICENSE). Built for academic dissertation purposes.
