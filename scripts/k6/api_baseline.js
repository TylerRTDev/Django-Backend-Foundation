// Baseline benchmark — API-level caching performance measurement.
//
// Profile: 50 RPS steady, 2 min duration, warm cache.
// Endpoints: /api/products/ (list, 70%) and /api/products/{slug}/ (detail, 30%)
// Metrics: p95 latency, RPS, failure rate, DB query reduction.
//
// Run via perf profile with K6_SCRIPT override:
//   K6_SCRIPT=api_baseline.js docker compose -f docker-compose.yaml -f docker-compose.perf.yaml run --rm k6
//
// Standalone:
//   docker run --rm --network django-backend-foundation_default \
//     -e BASE_URL=http://web:8000 \
//     -v ./scripts/k6:/scripts \
//     grafana/k6:latest run \
//     --out experimental-prometheus-rw \
//     /scripts/api_baseline.js

import http from "k6/http";
import { check, sleep } from "k6";
import { Rate, Trend } from "k6/metrics";

const BASE_URL = __ENV.BASE_URL || "http://web:8000";

export const options = {
  scenarios: {
    baseline: {
      executor: "constant-arrival-rate",
      rate: 50,
      timeUnit: "1s",
      duration: "2m",
      preAllocatedVUs: 20,
      maxVUs: 60,
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<500"],
  },
};

const failureRate = new Rate("baseline_failure_rate");
const latencyTrend = new Trend("baseline_latency_ms");

// Setup: fetch all product slugs once before the test starts.
// k6 calls setup() once, passes the return value to each VU's default().
export function setup() {
  const resp = http.get(`${BASE_URL}/api/products/?page_size=150`);
  const data = JSON.parse(resp.body);
  return { slugs: data.results.map((p) => p.slug) };
}

export default function (data) {
  if (Math.random() < 0.7) {
    hitList();
  } else {
    hitDetail(data.slugs);
  }
  sleep(1);
}

function hitList() {
  const page = (Math.floor(Math.random() * 3) + 1).toString();
  const resp = http.get(`${BASE_URL}/api/products/?page=${page}`, {
    tags: { name: "api_product_list", page: page },
  });

  latencyTrend.add(resp.timings.duration);

  check(resp, {
    "list status is 200": (r) => r.status === 200,
    "list returns results": (r) => {
      try { return JSON.parse(r.body).results !== undefined; }
      catch { return false; }
    },
    "list has 24 items": (r) => {
      try { return JSON.parse(r.body).results.length === 24; }
      catch { return false; }
    },
  });

  if (resp.status !== 200) {
    failureRate.add(1);
  } else {
    failureRate.add(0);
  }
}

function hitDetail(slugs) {
  const slug = slugs[Math.floor(Math.random() * slugs.length)];
  const resp = http.get(`${BASE_URL}/api/products/${slug}/`, {
    tags: { name: "api_product_detail", slug: slug },
  });

  latencyTrend.add(resp.timings.duration);

  check(resp, {
    "detail status is 200": (r) => r.status === 200,
    "detail returns product name": (r) => {
      try { return JSON.parse(r.body).name !== undefined; }
      catch { return false; }
    },
  });

  if (resp.status !== 200) {
    failureRate.add(1);
  } else {
    failureRate.add(0);
  }
}