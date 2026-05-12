/**
 * Local development API proxy.
 * Routes /api/xxx requests to the appropriate microservice.
 * Run: node proxy.js
 * Then set NEXT_PUBLIC_API_BASE_URL=http://localhost:9000 in .env.local
 */

const http = require("http");
const httpProxy = require("http-proxy");

const proxy = httpProxy.createProxyServer({});

// Route prefix → backend service
const ROUTES = [
  { prefix: "/api/auth",         target: "http://localhost:8001" },
  { prefix: "/api/users",        target: "http://localhost:8002" },
  { prefix: "/api/cases",        target: "http://localhost:8003" },
  { prefix: "/api/ai",           target: "http://localhost:8004" },
  { prefix: "/api/chatbot",      target: "http://localhost:8005" },
  { prefix: "/api/automation",   target: "http://localhost:8006" },
  { prefix: "/api/notifications",target: "http://localhost:8007" },
  { prefix: "/api/analytics",    target: "http://localhost:8008" },
  { prefix: "/api/files",        target: "http://localhost:8009" },
  { prefix: "/api/audit",        target: "http://localhost:8010" },
];

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
  "Access-Control-Allow-Headers": "Authorization,Content-Type",
};

const server = http.createServer((req, res) => {
  const origin = req.headers.origin || "http://localhost:3000";

  // Dynamic CORS — echo back the requesting origin (required for credentials: 'include')
  res.setHeader("Access-Control-Allow-Origin", origin);
  res.setHeader("Access-Control-Allow-Credentials", "true");
  res.setHeader("Access-Control-Allow-Methods", "GET,POST,PUT,PATCH,DELETE,OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Authorization,Content-Type,Accept");

  // Handle preflight
  if (req.method === "OPTIONS") {
    res.writeHead(204);
    res.end();
    return;
  }

  const url = req.url || "/";
  const route = ROUTES.find(r => url.startsWith(r.prefix));

  if (!route) {
    res.writeHead(404);
    res.end(JSON.stringify({ detail: `No route for ${url}` }));
    return;
  }

  // Rewrite URL: /api/auth/login → /auth/login
  req.url = url.replace("/api", "");

  proxy.web(req, res, { target: route.target, changeOrigin: true }, (err) => {
    if (!res.headersSent) {
      res.writeHead(502);
      res.end(JSON.stringify({ detail: `Service at ${route.target} unavailable: ${err.message}` }));
    }
  });
});

const PORT = 9000;
server.listen(PORT, () => {
  console.log(`\n🔀 Local API Proxy running on http://localhost:${PORT}`);
  console.log(`   Routing /api/* → microservices on :8001-:8010\n`);
  ROUTES.forEach(r => console.log(`   ${r.prefix.padEnd(26)} → ${r.target}`));
  console.log(`\n   Set in web-app/.env.local:`);
  console.log(`   NEXT_PUBLIC_API_BASE_URL=http://localhost:${PORT}\n`);
});

proxy.on("error", (err, req, res) => {
  if (!res.headersSent) {
    res.writeHead(502);
    res.end(JSON.stringify({ detail: err.message }));
  }
});
