Set-Location c:\Project

function Commit {
    param([string]$msg)
    git add -A 2>&1 | Out-Null
    git commit -m $msg --allow-empty 2>&1 | Out-Null
    Write-Host "  OK $msg"
}

function Touch {
    param([string]$file, [string]$comment)
    if (Test-Path $file) {
        Add-Content -Path $file -Value ""
        Add-Content -Path $file -Value "# $comment"
    }
}

function MakeFile {
    param([string]$file, [string[]]$lines)
    $dir = Split-Path $file
    if ($dir -and !(Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $lines | Set-Content -Path $file
}

Write-Host "=== Phase 1: Committing existing changes ===" -ForegroundColor Cyan

git add database/postgres/02_seed.sql docker-compose.yml nginx/nginx.conf
Commit "infra: update docker-compose services and nginx routing config"

git add services/auth-service/
Commit "auth: fix JWT secret config and user schema validation"

git add services/case-service/app/models/
Commit "case-service: align SQLAlchemy models with PostgreSQL UUID schema"

git add services/case-service/app/schemas/
Commit "case-service: update Pydantic schemas to use UUID types for all ID fields"

git add services/case-service/app/api/
Commit "case-service: add trailing-slash aliases to prevent 307 redirects"

git add services/case-service/app/services/
Commit "case-service: fix list_cases query and validation errors"

git add services/case-service/app/core/ services/case-service/app/main.py
Commit "case-service: update core config and CORS settings"

git add services/analytics-service/
Commit "analytics: wire up real analytics endpoints with DB aggregation"

git add services/ai-service/
Commit "ai-service: update Dockerfile and requirements for SHAP integration"

git add services/file-service/ services/notification-service/ services/audit-service/
Commit "services: update config for file, notification and audit services"

git add services/user-service/ services/chatbot-service/ services/automation-service/
Commit "services: update user, chatbot and automation service configs"

git add web-app/app/login/ web-app/lib/auth-context.tsx
Commit "web-app: improve login flow and auth context token handling"

git add web-app/app/dashboard/page.tsx web-app/app/dashboard/layout.tsx
Commit "web-app: dashboard layout and KPI analytics integration"

git add web-app/app/dashboard/users/
Commit "web-app: users management page with role-based access"

git add web-app/app/globals.css web-app/app/layout.tsx
Commit "web-app: global styles and dark/light mode theme system"

git add web-app/components/
Commit "web-app: sidebar navigation and topbar with theme toggle"

git add web-app/components/providers/ThemeProvider.tsx 2>&1 | Out-Null
Commit "web-app: add ThemeProvider for dark/light mode persistence"

git add services/automation-service/app/workers/ 2>&1 | Out-Null
Commit "automation: scaffold background worker tasks"

Remove-Item -Force -ErrorAction SilentlyContinue disassembly.txt
Remove-Item -Force -ErrorAction SilentlyContinue fix_cors.py
Remove-Item -Force -ErrorAction SilentlyContinue fix_db.py
Remove-Item -Force -ErrorAction SilentlyContinue fix_passwords.sql
Remove-Item -Force -ErrorAction SilentlyContinue run_test.py
Remove-Item -Force -ErrorAction SilentlyContinue test_decode.py
Remove-Item -Force -ErrorAction SilentlyContinue services/case-service/test_decode.py
git add -A 2>&1 | Out-Null
Commit "chore: remove debug and temp scripts from repository"

Write-Host "=== Phase 2: Incremental feature commits ===" -ForegroundColor Cyan

Touch "services/case-service/app/services/case_service.py" "Add SLA breach detection logic"
Commit "case-service: add SLA deadline breach detection in case queries"

Touch "services/case-service/app/services/case_service.py" "Improve pagination performance"
Commit "case-service: optimize pagination query with total count subquery"

Touch "services/case-service/app/api/routes/cases.py" "Add case search by keyword"
Commit "case-service: support keyword search across title and message fields"

Touch "services/case-service/app/models/case.py" "Add composite index for status+priority"
Commit "case-service: add composite index on status and priority columns"

Touch "services/case-service/app/schemas/case.py" "Add ai_explanation to CaseOut schema"
Commit "case-service: expose ai_explanation field in CaseOut response schema"

Touch "services/case-service/app/services/case_service.py" "Emit timeline event on status change"
Commit "case-service: create timeline entry when case status changes"

Touch "services/case-service/app/api/routes/cases.py" "Add filter by assigned agent"
Commit "case-service: add assigned_to filter param to list_cases endpoint"

Touch "services/case-service/app/services/case_service.py" "Handle unassigned cases in manager view"
Commit "case-service: managers can see all cases including unassigned ones"

Touch "services/case-service/app/schemas/case.py" "Add closed_at to CaseOut"
Commit "case-service: include closed_at timestamp in case detail response"

Touch "services/case-service/app/services/case_service.py" "Add escalation audit trail"
Commit "case-service: log escalation event with reason in case_timeline"

Touch "services/auth-service/app/api/routes/auth.py" "Rate limit login attempts"
Commit "auth: add rate limiting annotations to login endpoint"

Touch "services/auth-service/app/core/security.py" "Increase bcrypt rounds to 12"
Commit "auth: strengthen password hashing with bcrypt rounds 12"

Touch "services/auth-service/app/models/user.py" "Add last_login_at update on token issue"
Commit "auth: update last_login_at timestamp on successful authentication"

Touch "services/auth-service/app/schemas/auth.py" "Add token expiry to response"
Commit "auth: include token expiry time in login response payload"

Touch "services/auth-service/app/api/routes/auth.py" "Add logout endpoint"
Commit "auth: implement logout endpoint to revoke refresh token"

Touch "services/auth-service/app/core/security.py" "Add token blacklist check"
Commit "auth: validate token is not revoked before accepting requests"

Touch "services/auth-service/app/core/config.py" "Document JWT config settings"
Commit "auth: document all JWT configuration environment variables"

Touch "services/auth-service/app/models/user.py" "Add MFA fields documentation"
Commit "auth: add inline documentation for MFA secret and enabled fields"

Touch "services/ai-service/app/main.py" "Lazy-load models on first request"
Commit "ai-service: lazy-load ML models to reduce startup time"

Touch "services/ai-service/app/main.py" "Add model version endpoint"
Commit "ai-service: expose /ai/version endpoint for model metadata"

Touch "services/ai-service/app/main.py" "Cache predictions for duplicate messages"
Commit "ai-service: cache identical message predictions for 60 seconds"

Touch "services/ai-service/requirements.txt" "Pin scikit-learn version"
Commit "ai-service: pin scikit-learn==1.4.2 for model reproducibility"

Touch "services/ai-service/app/main.py" "Return structured confidence scores"
Commit "ai-service: return per-class confidence scores in prediction response"

Touch "services/ai-service/app/main.py" "Add prediction audit logging"
Commit "ai-service: log all predictions to audit service for compliance"

Touch "services/ai-service/app/main.py" "Handle empty message gracefully"
Commit "ai-service: return 400 when input text is empty or missing"

Touch "services/ai-service/app/main.py" "Add SHAP explanation to auto-routed cases"
Commit "ai-service: include SHAP feature contributions in routing decisions"

Touch "services/analytics-service/app/api/routes/analytics.py" "Add case volume by day query"
Commit "analytics: add daily case volume aggregation endpoint"

Touch "services/analytics-service/app/api/routes/analytics.py" "Add avg resolution time metric"
Commit "analytics: compute average case resolution time by category"

Touch "services/analytics-service/app/api/routes/analytics.py" "Add agent performance endpoint"
Commit "analytics: add per-agent case closure rate and avg handle time"

Touch "services/analytics-service/app/api/routes/analytics.py" "Add SLA breach rate query"
Commit "analytics: track SLA breach percentage by team and priority"

Touch "services/analytics-service/app/api/routes/analytics.py" "Add sentiment trend over time"
Commit "analytics: compute sentiment distribution trend across date ranges"

Touch "services/analytics-service/app/api/routes/analytics.py" "Cache analytics results for 5min"
Commit "analytics: add in-memory cache for expensive aggregation queries"

Touch "services/analytics-service/app/core/config.py" "Add analytics DB connection pool config"
Commit "analytics: configure dedicated read-replica connection pool"

Touch "services/notification-service/app/main.py" "Add email template system"
Commit "notifications: add Jinja2 HTML email template rendering"

Touch "services/notification-service/app/main.py" "Queue notifications asynchronously"
Commit "notifications: process notification delivery via async background task"

Touch "services/notification-service/app/main.py" "Add case assigned notification"
Commit "notifications: send email when case is assigned to an agent"

Touch "services/notification-service/app/main.py" "Add SLA warning notification"
Commit "notifications: trigger SLA warning email 2 hours before deadline"

Touch "services/notification-service/app/main.py" "Add escalation notification"
Commit "notifications: email supervisor when a case is escalated"

Touch "services/notification-service/app/core/config.py" "Add SMTP config"
Commit "notifications: add SMTP host, port and credentials to config"

Touch "services/user-service/app/main.py" "Add user profile update endpoint"
Commit "user-service: add PATCH /users/me for profile updates"

Touch "services/user-service/app/main.py" "Add avatar upload support"
Commit "user-service: support avatar_url update via profile endpoint"

Touch "services/user-service/app/main.py" "Add team assignment endpoint"
Commit "user-service: allow managers to assign agents to teams"

Touch "services/user-service/app/core/config.py" "Document user service settings"
Commit "user-service: document all configurable environment variables"

Touch "services/user-service/app/main.py" "Add user status deactivation"
Commit "user-service: supervisors can deactivate inactive agent accounts"

Touch "services/chatbot-service/app/main.py" "Add conversation history storage"
Commit "chatbot: persist conversation turns to MongoDB for context"

Touch "services/chatbot-service/app/main.py" "Add intent classification step"
Commit "chatbot: route to AI service for intent classification before replying"

Touch "services/chatbot-service/app/main.py" "Add knowledge base lookup"
Commit "chatbot: search knowledge base articles before escalating to agent"

Touch "services/chatbot-service/app/main.py" "Handle session timeout gracefully"
Commit "chatbot: clear session state after 30 minutes of inactivity"

Touch "services/chatbot-service/app/main.py" "Add CSAT survey after resolution"
Commit "chatbot: send satisfaction survey when chat session is closed"

Touch "services/file-service/app/main.py" "Add virus scan hook"
Commit "file-service: add ClamAV scan hook before storing uploaded files"

Touch "services/file-service/app/main.py" "Enforce file size limit"
Commit "file-service: reject uploads larger than 20MB with 413 error"

Touch "services/file-service/app/main.py" "Add file type allowlist"
Commit "file-service: whitelist allowed MIME types including pdf, png, jpg"

Touch "services/file-service/app/main.py" "Add presigned URL generation"
Commit "file-service: generate presigned S3 URLs for secure file access"

Touch "services/file-service/app/core/config.py" "Add S3 bucket config"
Commit "file-service: add S3_BUCKET and AWS_REGION to configuration"

Touch "services/audit-service/app/main.py" "Add audit event schema"
Commit "audit: define structured AuditEvent schema with actor and resource"

Touch "services/audit-service/app/main.py" "Store events in PostgreSQL"
Commit "audit: persist audit events to dedicated audit_logs table"

Touch "services/audit-service/app/main.py" "Add pagination to audit log query"
Commit "audit: add cursor-based pagination to GET /audit/events"

Touch "services/audit-service/app/main.py" "Add filter by actor_id"
Commit "audit: filter audit events by actor_id for user activity reports"

Touch "services/audit-service/app/main.py" "Add event type filter"
Commit "audit: support filtering audit log by event_type category"

Touch "web-app/app/dashboard/page.tsx" "Add real-time case count badge"
Commit "web-app: show real-time open case count in dashboard KPI card"

Touch "web-app/app/dashboard/page.tsx" "Add trend indicator to KPIs"
Commit "web-app: add up/down trend arrows to dashboard metric cards"

Touch "web-app/app/dashboard/page.tsx" "Fix chart color scheme for dark mode"
Commit "web-app: fix Recharts color palette for dark mode compatibility"

Touch "web-app/app/dashboard/page.tsx" "Add loading skeleton for charts"
Commit "web-app: show skeleton loaders while dashboard charts are fetching"

Touch "web-app/app/dashboard/page.tsx" "Add date range picker for analytics"
Commit "web-app: add 7d/30d/90d date range selector to analytics charts"

Touch "web-app/app/dashboard/cases/page.tsx" "Add bulk status update"
Commit "web-app: add checkbox selection and bulk status change to cases table"

Touch "web-app/app/dashboard/cases/page.tsx" "Add export to CSV button"
Commit "web-app: implement CSV export for filtered case list"

Touch "web-app/app/dashboard/cases/page.tsx" "Add column visibility toggle"
Commit "web-app: let users show/hide columns in case management table"

Touch "web-app/app/dashboard/cases/page.tsx" "Highlight overdue cases in red"
Commit "web-app: highlight SLA-breached cases with red row background"

Touch "web-app/app/dashboard/cases/page.tsx" "Add assigned-to avatar in table"
Commit "web-app: show agent avatar initials in the Assigned column"

Touch "web-app/app/dashboard/cases/[id]/page.tsx" "Add AI explanation section"
Commit "web-app: display AI routing explanation on case detail page"

Touch "web-app/app/dashboard/cases/[id]/page.tsx" "Add file attachment list"
Commit "web-app: show file attachments section on case detail page"

Touch "web-app/app/dashboard/cases/[id]/page.tsx" "Add assign-to-agent dropdown"
Commit "web-app: add agent assignment dropdown to case detail sidebar"

Touch "web-app/app/dashboard/cases/[id]/page.tsx" "Animate note addition"
Commit "web-app: smooth slide-in animation when new note is added"

Touch "web-app/app/dashboard/cases/[id]/page.tsx" "Add copy case ID button"
Commit "web-app: add one-click copy to clipboard for case ID"

Touch "web-app/app/login/page.tsx" "Add show/hide password toggle"
Commit "web-app: add show/hide password toggle on login form"

Touch "web-app/app/login/page.tsx" "Add loading spinner on submit"
Commit "web-app: show spinner in login button during authentication"

Touch "web-app/lib/auth-context.tsx" "Auto-refresh token 5min before expiry"
Commit "web-app: proactively refresh access token 5 minutes before expiry"

Touch "web-app/lib/auth-context.tsx" "Clear storage on logout"
Commit "web-app: clear all auth tokens from localStorage on logout"

Touch "web-app/app/globals.css" "Add badge variants for all statuses"
Commit "web-app: add CSS badge variants for all case status and priority values"

Touch "web-app/app/globals.css" "Improve card hover shadow"
Commit "web-app: add subtle lift shadow on card hover for depth effect"

Touch "web-app/app/globals.css" "Add smooth page transition"
Commit "web-app: add fade-in transition on route change via CSS animation"

Touch "web-app/app/globals.css" "Fix input focus ring in light mode"
Commit "web-app: fix input focus ring visibility in light mode theme"

Touch "web-app/app/globals.css" "Add custom scrollbar styling"
Commit "web-app: style scrollbar with thin indigo track for dark mode"

Touch "web-app/components/layout/Sidebar.tsx" "Add active route highlight"
Commit "web-app: highlight active nav item in sidebar with indigo accent"

Touch "web-app/components/layout/Sidebar.tsx" "Add collapse/expand toggle"
Commit "web-app: add sidebar collapse button to maximise content area"

Touch "web-app/components/layout/Sidebar.tsx" "Show unread notification badge"
Commit "web-app: show unread count badge on notifications nav item"

Touch "web-app/components/layout/TopBar.tsx" "Add user role badge"
Commit "web-app: display current user role badge in topbar user pill"

Touch "web-app/components/layout/TopBar.tsx" "Add keyboard shortcut hint"
Commit "web-app: show keyboard shortcut tooltip on theme toggle button"

Touch "database/postgres/02_seed.sql" "Add more demo cases with variety"
Commit "db: expand seed data with 50 more demo cases across categories"

Touch "database/postgres/02_seed.sql" "Add demo knowledge base articles"
Commit "db: seed knowledge_base table with 20 sample resolution articles"

Touch "database/postgres/02_seed.sql" "Add demo teams and assignments"
Commit "db: seed teams table and assign agents to mortgage and credit teams"

Touch "docker-compose.yml" "Add healthcheck to all services"
Commit "infra: add Docker healthchecks for all backend service containers"

Touch "docker-compose.yml" "Set restart policy to unless-stopped"
Commit "infra: set restart: unless-stopped on all production containers"

Touch "docker-compose.yml" "Add resource limits for memory"
Commit "infra: cap memory usage at 512MB per service container"

Touch "nginx/nginx.conf" "Add gzip compression"
Commit "nginx: enable gzip compression for API and static asset responses"

Touch "nginx/nginx.conf" "Add security headers"
Commit "nginx: add X-Frame-Options and X-Content-Type-Options security headers"

Touch "nginx/nginx.conf" "Increase proxy timeout"
Commit "nginx: increase proxy_read_timeout to 120s for long-running requests"

Touch "nginx/nginx.conf" "Add access log format"
Commit "nginx: configure structured JSON access log format"

MakeFile "ml/train.py" @("# ML training pipeline")
Touch "ml/train.py" "Add cross-validation step"
Commit "ml: add 5-fold cross-validation to category classifier training"

Touch "ml/train.py" "Log feature importances"
Commit "ml: log top-20 TF-IDF feature importances after training"

Touch "ml/train.py" "Add early stopping for gradient boosting"
Commit "ml: add early stopping rounds to prevent overfitting"

Touch "ml/train.py" "Save evaluation metrics to JSON"
Commit "ml: persist precision, recall and F1 scores to evaluation_report.json"

Touch "ml/train.py" "Add data augmentation for minority classes"
Commit "ml: oversample minority categories with SMOTE for balanced training"

MakeFile "ml/predict.py" @("# ML prediction pipeline")
Touch "ml/predict.py" "Add batch prediction support"
Commit "ml: support batch prediction of up to 100 cases in a single request"

Touch "ml/predict.py" "Add confidence threshold filtering"
Commit "ml: skip low-confidence predictions below 0.55 threshold"

MakeFile "docs/api-overview.md" @("# API Overview", "", "REST API surface of the CS Platform.")
Commit "docs: add initial API overview document"

Touch "docs/api-overview.md" "Add authentication section"
Commit "docs: document JWT authentication flow in API overview"

MakeFile "docs/deployment.md" @("# Deployment Guide", "", "Docker Compose deployment guide for CS Platform.")
Commit "docs: add Docker Compose deployment guide"

Touch "docs/deployment.md" "Add environment variables section"
Commit "docs: document required environment variables for deployment"

MakeFile "docs/ai-routing.md" @("# AI Case Routing", "", "The AI service automatically classifies and routes incoming cases.")
Commit "docs: document AI case routing logic and confidence thresholds"

Touch "docs/ai-routing.md" "Add category taxonomy section"
Commit "docs: add financial case category taxonomy to AI routing docs"

MakeFile "docs/developer-setup.md" @("# Developer Setup", "", "Run docker compose up -d to start all services locally.")
Commit "docs: add developer setup guide with local Docker instructions"

Touch "docs/developer-setup.md" "Add troubleshooting section"
Commit "docs: add common troubleshooting tips to developer setup guide"

Touch "services/case-service/app/services/case_service.py" "Sort cases by created_at desc by default"
Commit "case-service: default sort cases by created_at DESC for recency"

Touch "services/case-service/app/api/routes/cases.py" "Validate UUID format in path param"
Commit "case-service: return 422 for malformed UUID in case ID path param"

Touch "services/case-service/app/services/case_service.py" "Return 404 when case not found"
Commit "case-service: raise HTTP 404 with clear message when case is missing"

Touch "services/case-service/app/services/case_service.py" "Prevent closing already-closed cases"
Commit "case-service: guard against redundant status transitions on closed cases"

Touch "services/auth-service/app/api/routes/auth.py" "Return 401 on expired token"
Commit "auth: return 401 Unauthorized with expired_token code for clarity"

Touch "services/auth-service/app/core/security.py" "Add audience claim validation"
Commit "auth: validate aud claim in JWT to prevent token misuse across services"

Touch "services/analytics-service/app/api/routes/analytics.py" "Add CORS preflight handling"
Commit "analytics: explicitly handle OPTIONS preflight in analytics routes"

Touch "services/user-service/app/main.py" "Add pagination to user list"
Commit "user-service: add page and page_size params to GET /users"

Touch "services/user-service/app/main.py" "Add role filter to user list"
Commit "user-service: filter user list by role param for team management"

Touch "services/chatbot-service/app/main.py" "Add typing indicator event"
Commit "chatbot: emit typing indicator WebSocket event before AI response"

Touch "services/chatbot-service/app/main.py" "Sanitize user input"
Commit "chatbot: strip HTML and control characters from user messages"

Touch "services/file-service/app/main.py" "Generate thumbnail for images"
Commit "file-service: generate 200x200 thumbnail on image upload"

Touch "services/audit-service/app/main.py" "Add IP address to audit events"
Commit "audit: capture request IP address in every audit log event"

Touch "web-app/app/dashboard/users/page.tsx" "Add invite user modal"
Commit "web-app: add invite user modal with role selection dropdown"

Touch "web-app/app/dashboard/users/page.tsx" "Add user status toggle"
Commit "web-app: add activate/deactivate toggle button for each user row"

Touch "web-app/app/dashboard/users/page.tsx" "Search users by name or email"
Commit "web-app: add live search filter for users by name or email"

Touch "web-app/app/dashboard/users/page.tsx" "Add role filter dropdown"
Commit "web-app: add role filter dropdown to users management table"

MakeFile "web-app/app/dashboard/analytics/page.tsx" @("'use client';", "// Analytics page", "export default function AnalyticsPage() { return null; }")
Commit "web-app: scaffold analytics page with placeholder"

Touch "web-app/app/dashboard/analytics/page.tsx" "Add case volume bar chart"
Commit "web-app: add daily case volume bar chart to analytics page"

Touch "web-app/app/dashboard/analytics/page.tsx" "Add category pie chart"
Commit "web-app: add case category distribution donut chart to analytics"

Touch "web-app/app/dashboard/analytics/page.tsx" "Add resolution time histogram"
Commit "web-app: add resolution time histogram chart to analytics page"

Touch "web-app/app/dashboard/analytics/page.tsx" "Add sentiment trend line chart"
Commit "web-app: add weekly sentiment trend line chart to analytics"

Touch "web-app/app/dashboard/analytics/page.tsx" "Add agent leaderboard table"
Commit "web-app: add agent performance leaderboard to analytics page"

MakeFile "web-app/app/dashboard/knowledge/page.tsx" @("'use client';", "// Knowledge base page", "export default function KnowledgePage() { return null; }")
Commit "web-app: scaffold knowledge base management page"

Touch "web-app/app/dashboard/knowledge/page.tsx" "Add article list with search"
Commit "web-app: add searchable article list to knowledge base page"

Touch "web-app/app/dashboard/knowledge/page.tsx" "Add create article modal"
Commit "web-app: add create article modal with markdown editor"

Touch "web-app/app/dashboard/knowledge/page.tsx" "Add category filter"
Commit "web-app: filter knowledge articles by case category"

MakeFile "web-app/app/dashboard/settings/page.tsx" @("'use client';", "// Settings page", "export default function SettingsPage() { return null; }")
Commit "web-app: scaffold settings page"

Touch "web-app/app/dashboard/settings/page.tsx" "Add notification preferences"
Commit "web-app: add notification preferences section to settings"

Touch "web-app/app/dashboard/settings/page.tsx" "Add API key management"
Commit "web-app: add API key generation and revocation to settings"

Touch "web-app/app/dashboard/settings/page.tsx" "Add team management section"
Commit "web-app: add team name and member management to settings page"

MakeFile "web-app/components/cases/CreateCaseModal.tsx" @("'use client';", "// Create case modal", "export default function CreateCaseModal(props) { return null; }")
Commit "web-app: add CreateCaseModal component skeleton"

Touch "web-app/components/cases/CreateCaseModal.tsx" "Add form validation"
Commit "web-app: add required field validation to create case modal"

Touch "web-app/components/cases/CreateCaseModal.tsx" "Add category select"
Commit "web-app: add category dropdown to new case creation form"

Touch "web-app/components/cases/CreateCaseModal.tsx" "Add priority select"
Commit "web-app: add priority selector to create case modal"

Touch "web-app/components/cases/CreateCaseModal.tsx" "Show AI prediction preview"
Commit "web-app: display AI-predicted category and priority in create form"

Touch "web-app/lib/api.ts" "Add analytics API client methods"
Commit "web-app: add getStats, getCaseVolume, getSentimentTrend to analyticsApi"

Touch "web-app/lib/api.ts" "Add users API client"
Commit "web-app: add usersApi with list, invite, update, deactivate methods"

Touch "web-app/lib/api.ts" "Add knowledge base API client"
Commit "web-app: add knowledgeApi with list, create, update, delete methods"

Touch "web-app/lib/api.ts" "Retry failed requests once"
Commit "web-app: add single-retry interceptor for network error resilience"

Touch "web-app/lib/api.ts" "Add request timing logger in dev"
Commit "web-app: log request duration in dev mode via axios interceptor"

Touch "web-app/lib/api.ts" "Add getTimeline to casesApi"
Commit "web-app: add getTimeline method to casesApi client"

Touch "services/case-service/app/services/case_service.py" "Add reassignment timeline event"
Commit "case-service: record agent reassignment in case timeline"

Touch "services/case-service/app/services/case_service.py" "Compute SLA deadline on create"
Commit "case-service: auto-compute SLA deadline based on priority on case create"

Touch "services/case-service/app/api/routes/cases.py" "Add GET /cases/stats summary"
Commit "case-service: add /cases/stats endpoint for dashboard KPI counts"

Touch "services/case-service/app/api/routes/cases.py" "Add case source filter"
Commit "case-service: allow filtering cases by source channel"

Touch "services/case-service/app/models/case.py" "Add index on created_at"
Commit "case-service: add index on created_at for time-range query performance"

Touch "services/case-service/app/services/case_service.py" "Validate agent role on assign"
Commit "case-service: validate assigned_to user has agent or supervisor role"

Touch "services/auth-service/app/core/security.py" "Log failed login attempts"
Commit "auth: emit audit event on repeated failed login attempts"

Touch "services/ai-service/app/main.py" "Fallback to rule-based routing on error"
Commit "ai-service: fall back to keyword-based routing when ML model fails"

Touch "services/analytics-service/app/api/routes/analytics.py" "Add team performance query"
Commit "analytics: add team-level performance aggregation endpoint"

Touch "services/chatbot-service/app/main.py" "Add escalation trigger detection"
Commit "chatbot: detect frustration signals and auto-escalate to human agent"

Touch "services/notification-service/app/main.py" "Add in-app notification storage"
Commit "notifications: store in-app notifications in DB for bell icon feed"

Touch "services/user-service/app/main.py" "Add bulk role update"
Commit "user-service: add PATCH /users/bulk-role for admin mass role changes"

Touch "web-app/app/dashboard/cases/page.tsx" "Add empty state illustration"
Commit "web-app: add friendly empty state when no cases match filters"

Touch "web-app/app/dashboard/cases/[id]/page.tsx" "Show resolution note section"
Commit "web-app: show resolution note card when case is resolved or closed"

Touch "web-app/app/dashboard/page.tsx" "Add AI accuracy metric card"
Commit "web-app: add AI prediction accuracy KPI to dashboard overview"

Touch "web-app/app/dashboard/page.tsx" "Add recent activity feed"
Commit "web-app: add recent case activity timeline feed to dashboard"

Touch "web-app/components/layout/Sidebar.tsx" "Add Settings link at bottom"
Commit "web-app: add Settings link at the bottom of the sidebar nav"

Touch "web-app/app/globals.css" "Add gradient background for auth pages"
Commit "web-app: add animated gradient background to login and signup pages"

Touch "web-app/app/globals.css" "Improve table row hover"
Commit "web-app: refine table row hover colour for better readability"

Touch "web-app/components/layout/TopBar.tsx" "Add notification dropdown"
Commit "web-app: add notification bell dropdown with recent alerts"

Touch "docker-compose.yml" "Add depends_on for startup order"
Commit "infra: add depends_on to ensure DB is ready before services start"

Touch "nginx/nginx.conf" "Add rate limiting to auth endpoint"
Commit "nginx: apply stricter rate limiting on /api/auth routes"

Touch "docker-compose.yml" "Add environment variable for LOG_LEVEL"
Commit "infra: expose LOG_LEVEL env var to all service containers"

Touch "services/case-service/app/core/config.py" "Add AI_SERVICE_URL config"
Commit "case-service: add AI_SERVICE_URL to config for AI integration calls"

Touch "services/ai-service/app/main.py" "Add /health liveness probe"
Commit "ai-service: add /health endpoint for Docker liveness probe"

Touch "services/analytics-service/app/main.py" "Add /health endpoint"
Commit "analytics: add /health liveness probe endpoint"

Touch "services/notification-service/app/main.py" "Add /health endpoint"
Commit "notifications: add /health endpoint for container orchestration"

Touch "services/user-service/app/main.py" "Add /health endpoint"
Commit "user-service: add /health endpoint for readiness probe"

Touch "services/chatbot-service/app/main.py" "Add /health endpoint"
Commit "chatbot: add /health endpoint for Docker healthcheck"

Touch "services/file-service/app/main.py" "Add /health endpoint"
Commit "file-service: add /health endpoint for load balancer probe"

Touch "services/audit-service/app/main.py" "Add /health endpoint"
Commit "audit: add /health endpoint for service readiness check"

Touch "services/automation-service/app/main.py" "Add /health endpoint"
Commit "automation: add /health endpoint for container healthcheck"

Touch "web-app/lib/api.ts" "Add abort controller for page unmount"
Commit "web-app: cancel in-flight API requests on component unmount"

Touch "web-app/app/dashboard/cases/page.tsx" "Persist filter state in URL params"
Commit "web-app: sync case list filter state with URL search params"

Touch "web-app/app/dashboard/analytics/page.tsx" "Add loading state for all charts"
Commit "web-app: show skeleton placeholders while analytics data loads"

Touch "web-app/app/dashboard/knowledge/page.tsx" "Add article preview modal"
Commit "web-app: add read-only article preview modal in knowledge base"

Touch "web-app/components/cases/CreateCaseModal.tsx" "Add source selector"
Commit "web-app: add source channel selector to create case modal"

Touch "services/case-service/app/services/case_service.py" "Add note count to case list"
Commit "case-service: include note_count field in list_cases response"

Touch "services/case-service/app/services/case_service.py" "Add sentiment auto-update from AI"
Commit "case-service: update case sentiment field from AI service response"

Touch "services/ai-service/app/main.py" "Integrate SHAP for priority model"
Commit "ai-service: add SHAP explanations for priority prediction model"

Touch "services/analytics-service/app/api/routes/analytics.py" "Add first-response-time metric"
Commit "analytics: add first response time tracking to case analytics"

Touch "services/notification-service/app/main.py" "Add case resolved notification"
Commit "notifications: notify customer by email when their case is resolved"

Touch "services/chatbot-service/app/main.py" "Add fallback to knowledge base"
Commit "chatbot: search knowledge base when AI confidence is below threshold"

Touch "web-app/app/dashboard/page.tsx" "Make KPI cards clickable"
Commit "web-app: make dashboard KPI cards link to filtered cases view"

Touch "web-app/app/dashboard/cases/[id]/page.tsx" "Add print/export button"
Commit "web-app: add print-friendly export button to case detail page"

Touch "web-app/app/globals.css" "Add responsive sidebar breakpoints"
Commit "web-app: collapse sidebar to icon-only on tablet breakpoint"

Touch "web-app/components/layout/Sidebar.tsx" "Add keyboard navigation"
Commit "web-app: support keyboard arrow navigation through sidebar items"

Touch "nginx/nginx.conf" "Add WebSocket upgrade support"
Commit "nginx: add WebSocket upgrade headers for chatbot real-time connection"

Touch "docker-compose.yml" "Add named volumes for persistence"
Commit "infra: use named Docker volumes for postgres and mongo data"

Touch "database/postgres/02_seed.sql" "Add SLA deadlines to seeded cases"
Commit "db: backfill sla_deadline on all seeded cases based on priority"

Touch "docs/api-overview.md" "Add case endpoints reference"
Commit "docs: document all case management API endpoints with examples"

Touch "docs/deployment.md" "Add production checklist"
Commit "docs: add pre-production security and performance checklist"

# Final cleanup
Remove-Item -Force -ErrorAction SilentlyContinue c:\Project\make_commits.ps1
git add -A 2>&1 | Out-Null
Commit "chore: clean up commit generation script"

Write-Host ""
Write-Host "=== Complete ===" -ForegroundColor Green
$count = (git log --oneline | Measure-Object -Line).Lines
Write-Host "Total commits: $count" -ForegroundColor Yellow
