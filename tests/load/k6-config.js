import http from "k6/http";
import { check, sleep } from "k6";
import { Rate, Trend } from "k6/metrics";

const BASE_URL = __ENV.K6_TARGET_URL || "http://localhost:8000";

const errorRate = new Rate("errors");
const latency = new Trend("api_latency");

export const options = {
  stages: [
    { duration: "2m", target: 100 },
    { duration: "5m", target: 500 },
    { duration: "3m", target: 1000 },
    { duration: "5m", target: 1000 },
    { duration: "2m", target: 0 },
  ],
  thresholds: {
    http_req_duration: ["p(95)<500", "p(99)<1000"],
    errors: ["rate<0.01"],
    http_req_failed: ["rate<0.01"],
  },
};

export default function () {
  const endpoints = [
    { name: "health", path: "/health", method: "GET" },
    { name: "scripts", path: "/api/v1/scripts", method: "GET" },
    { name: "latest", path: "/api/v1/scripts/latest", method: "GET" },
    { name: "feed_rss", path: "/feed/rss", method: "GET" },
    { name: "search", path: "/api/v1/search?q=technology&limit=10", method: "GET" },
  ];

  const endpoint = endpoints[Math.floor(Math.random() * endpoints.length)];

  const start = Date.now();
  const res = http.get(`${BASE_URL}${endpoint.path}`, {
    tags: { name: endpoint.name },
    timeout: "10s",
  });
  latency.add(Date.now() - start);

  const success = check(res, {
    "status is 200": (r) => r.status === 200,
    "response time < 500ms": (r) => r.timings.duration < 500,
    "has body": (r) => r.body && r.body.length > 0,
  });

  errorRate.add(!success);
  sleep(Math.random() * 2 + 0.5);
}

export function handleSummary(data) {
  return {
    stdout: JSON.stringify(
      {
        total_requests: data.metrics.http_reqs.values.count,
        avg_duration_ms: Math.round(data.metrics.http_req_duration.values.avg),
        p95_duration_ms: Math.round(data.metrics.http_req_duration.values["p(95)"]),
        p99_duration_ms: Math.round(data.metrics.http_req_duration.values["p(99)"]),
        error_rate: data.metrics.http_req_failed.values.rate,
        max_vus: data.metrics.vus_max.values.max,
      },
      null,
      2
    ),
  };
}
