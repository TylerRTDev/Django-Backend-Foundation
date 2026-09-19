// Smoke test — quick validation of API endpoints and monitoring dashboard.
//
// Purpose: Verify endpoints respond, cache works, and metrics flow to
// Prometheus/Grafana before running heavier benchmarks.
//
// Profile: 5 RPS steady, 30s duration, 2 VUs max.
// Endpoints: /api/products/ (list) and /api/products/{slug}/ (detail)
//
// Run via perf profile:
//   docker compose -f docker-compose.yaml -f docker-compose.perf.yaml up
//
// Or standalone (with stack already running):
//   k6 run --out output-prometheus-remotewrite=http://prometheus:9090/api/v1/write scripts/k6/smoke.js

import http from "k6/http";
import { check, sleep } from "k6";
import { Rate } from "k6/metrics";

const BASE_URL = __ENV.BASE_URL || "http://web:8000";

export const options = {
  scenarios: {
    smoke: {
      executor: "constant-arrival-rate",
      rate: 5,              // 5 requests per second
      timeUnit: "1s",
      duration: "30s",      // 30 seconds — quick validation
      preAllocatedVUs: 2,
      maxVUs: 4,
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.05"],
    http_req_duration: ["p(95)<2000"],
  },
};

const failureRate = new Rate("smoke_failure_rate");

export default function () {
  // Step 1: Fetch product list
  const listResp = http.get(`${BASE_URL}/api/products/`, {
    tags: { name: "api_product_list" },
  });

  check(listResp, {
    "list status is 200": (r) => r.status === 200,
    "list returns results": (r) => {
      try { return JSON.parse(r.body).results !== undefined; }
      catch { return false; }
    },
  });

  if (listResp.status !== 200) {
    failureRate.add(1);
    sleep(1);
    return;
  }

  failureRate.add(0);

  // Step 2: If products exist, fetch first product detail
  let body;
  try { body = JSON.parse(listResp.body); } catch { sleep(1); return; }

  if (body.results && body.results.length > 0) {
    const slug = body.results[0].slug;
    const detailResp = http.get(`${BASE_URL}/api/products/${slug}/`, {
      tags: { name: "api_product_detail" },
    });

    check(detailResp, {
      "detail status is 200": (r) => r.status === 200,
      "detail returns product name": (r) => {
        try { return JSON.parse(r.body).name !== undefined; }
        catch { return false; }
      },
    });

    if (detailResp.status !== 200) {
      failureRate.add(1);
    } else {
      failureRate.add(0);
    }
  }

  sleep(1);
}