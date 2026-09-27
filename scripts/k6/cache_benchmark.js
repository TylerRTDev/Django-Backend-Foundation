// cache_benchmark.js — comprehensive caching benchmark for dev[ldn].
//
// One script, six phases, selected with PHASE. Each phase is a separate k6
// run so the cache can be flushed between them (k6 cannot flush memcached).
// Orchestrate with run_cache_suite.sh rather than invoking this directly.
//
//   PHASE=capacity   ramping arrival rate until degradation — finds the ceiling
//   PHASE=coldwarm   single-VU miss-vs-hit cost per endpoint
//   PHASE=steady     sustained load across several TTL cycles
//   PHASE=stampede   synchronised bursts at TTL boundaries (the ADR's core claim)
//   PHASE=variant    HTMX vs full-page cache key isolation (correctness)
//   PHASE=keyspace   large key space — eviction and hit-rate degradation
//
// Requires the X-Cache header patch (see cache_dogpile_xcache.patch.md).
// Without it every phase still runs, but cache state is reported as UNKNOWN
// and the stampede phase proves nothing.

import http from "k6/http";
import { check, sleep, fail } from "k6";
import { Counter, Rate, Trend } from "k6/metrics";

// ---------------------------------------------------------------- config

const BASE_URL = __ENV.BASE_URL || "http://web:8000";
const PHASE = __ENV.PHASE || "steady";

// TTLs must match core/cache_dogpile.py decorators in products/views.py.
const TTL_LIST = Number(__ENV.TTL_LIST || 60); // dogpile_cache on product_list
const TTL_GRID = Number(__ENV.TTL_GRID || 60); // dogpile_cache_swr on product_grid
const TTL_DETAIL = Number(__ENV.TTL_DETAIL || 180);

// Set from the capacity phase result. Default sized for a multi-core desktop
// host; drop to ~20 if running the whole stack on a Pi.
const RATE = Number(__ENV.RATE || 100);
const BURST_VUS = Number(__ENV.BURST_VUS || 100);
const DURATION = __ENV.DURATION || "5m";

// stampede target: "list" (short-wait dogpile) or "grid" (SWR)
const TARGET = __ENV.TARGET || "list";

// ---------------------------------------------------------------- metrics
//
// Low cardinality only. `endpoint` has ~5 values; never tag on slug or page.

const cacheHit = new Rate("cache_hit");
const cacheStale = new Rate("cache_stale");
const cacheBypass = new Rate("cache_bypass");
const cacheUnknown = new Rate("cache_unknown");

const recomputes = new Counter("cache_recomputes"); // X-Cache: MISS
const lockWaits = new Counter("cache_lock_waits");  // X-Cache: WAIT
const staleServed = new Counter("cache_stale_served");

const missLatency = new Trend("cache_miss_latency", true);
const hitLatency = new Trend("cache_hit_latency", true);
const staleLatency = new Trend("cache_stale_latency", true);

// ---------------------------------------------------------------- helpers

function record(res, endpoint) {
  const state = res.headers["X-Cache"] || "UNKNOWN";
  const t = { endpoint: endpoint };

  cacheHit.add(state === "HIT", t);
  cacheStale.add(state === "STALE", t);
  cacheBypass.add(state === "BYPASS", t);
  cacheUnknown.add(state === "UNKNOWN", t);

  if (state === "MISS") {
    recomputes.add(1, t);
    missLatency.add(res.timings.duration, t);
  } else if (state === "HIT") {
    hitLatency.add(res.timings.duration, t);
  } else if (state === "STALE") {
    staleServed.add(1, t);
    staleLatency.add(res.timings.duration, t);
  } else if (state === "WAIT") {
    lockWaits.add(1, t);
  }
  return state;
}

function getList(page) {
  return http.get(`${BASE_URL}/products/?page=${page}`, {
    tags: { name: "html_product_list" },
  });
}

function getGrid(page) {
  return http.get(`${BASE_URL}/products/grid/?page=${page}`, {
    headers: { "HX-Request": "true" },
    tags: { name: "htmx_product_grid" },
  });
}

function getDetail(slug) {
  return http.get(`${BASE_URL}/products/${slug}/`, {
    tags: { name: "html_product_detail" },
  });
}

function getApiList(page) {
  return http.get(`${BASE_URL}/api/products/?page=${page}`, {
    tags: { name: "api_product_list" },
  });
}

function getApiDetail(slug) {
  return http.get(`${BASE_URL}/api/products/${slug}/`, {
    tags: { name: "api_product_detail" },
  });
}

// The stampede phase targets exactly one key so the boundary is unambiguous.
function hitTarget() {
  return TARGET === "grid" ? getGrid(1) : getList(1);
}
const TARGET_ENDPOINT = TARGET === "grid" ? "htmx_product_grid" : "html_product_list";
const TARGET_TTL = TARGET === "grid" ? TTL_GRID : TTL_LIST;

// ---------------------------------------------------------------- setup

export function setup() {
  // Discover slugs once. Tagged "setup" so it can be excluded from latency
  // panels — it is one uncached 150-product fetch and skews percentiles.
  const resp = http.get(`${BASE_URL}/api/products/?page_size=150`, {
    tags: { name: "setup" },
  });
  if (resp.status !== 200) {
    fail(`setup: /api/products/ returned ${resp.status} — is the app up?`);
  }
  let slugs = [];
  try {
    slugs = JSON.parse(resp.body).results.map((p) => p.slug);
  } catch (e) {
    fail(`setup: could not parse product list: ${e}`);
  }
  if (slugs.length === 0) fail("setup: no products — run seed_products first");

  console.log(`PHASE=${PHASE} TARGET=${TARGET} slugs=${slugs.length} RATE=${RATE}`);
  return { slugs: slugs };
}

// ---------------------------------------------------------------- scenarios

const SCENARIOS = {
  // Phase 0 — find the ceiling. Everything else must run below it, or you are
  // measuring queueing rather than caching.
  capacity: {
    capacity_ramp: {
      executor: "ramping-arrival-rate",
      exec: "mixedTraffic",
      startRate: 10,
      timeUnit: "1s",
      preAllocatedVUs: 50,
      maxVUs: 600,
      stages: [
        { target: 25, duration: "30s" },
        { target: 50, duration: "30s" },
        { target: 100, duration: "30s" },
        { target: 200, duration: "30s" },
        { target: 400, duration: "30s" },
        { target: 700, duration: "30s" },
      ],
    },
  },

  // Phase 1 — what does a miss cost vs a hit? Single VU: latency, not queueing.
  coldwarm: {
    cold_warm_probe: {
      executor: "per-vu-iterations",
      exec: "coldWarmProbe",
      vus: 1,
      iterations: 1,
      maxDuration: "10m",
    },
  },

  // Phase 2 — sustained load across several TTL cycles.
  steady: {
    steady_state: {
      executor: "constant-arrival-rate",
      exec: "mixedTraffic",
      rate: RATE,
      timeUnit: "1s",
      duration: DURATION,
      preAllocatedVUs: Math.max(10, RATE),
      maxVUs: Math.max(30, RATE * 3),
    },
  },

  // Phase 3 — the ADR's core claim. Warm one key, then fire synchronised
  // bursts just after each TTL expiry. Exactly one MISS per burst = the lock
  // worked. N MISSes = a stampede.
  stampede: {
    stampede_warm: {
      executor: "shared-iterations",
      exec: "warmTarget",
      vus: 1,
      iterations: 1,
      startTime: "0s",
      maxDuration: "15s",
    },
    stampede_burst_1: {
      executor: "shared-iterations",
      exec: "burstTarget",
      vus: BURST_VUS,
      iterations: BURST_VUS,
      startTime: `${TARGET_TTL + 2}s`,
      maxDuration: "30s",
    },
    stampede_burst_2: {
      executor: "shared-iterations",
      exec: "burstTarget",
      vus: BURST_VUS,
      iterations: BURST_VUS,
      startTime: `${2 * TARGET_TTL + 4}s`,
      maxDuration: "30s",
    },
    stampede_burst_3: {
      executor: "shared-iterations",
      exec: "burstTarget",
      vus: BURST_VUS,
      iterations: BURST_VUS,
      startTime: `${3 * TARGET_TTL + 6}s`,
      maxDuration: "30s",
    },
  },

  // Phase 4 — correctness, not performance. Variant-aware keys must keep the
  // HTMX fragment and the full page from colliding.
  variant: {
    variant_isolation: {
      executor: "constant-arrival-rate",
      exec: "variantProbe",
      rate: 5,
      timeUnit: "1s",
      duration: "60s",
      preAllocatedVUs: 5,
      maxVUs: 15,
    },
  },

  // Phase 5 — key-space pressure. Walk every page and every slug so the
  // working set far exceeds the hot set; watch evictions and hit rate.
  keyspace: {
    keyspace_walk: {
      executor: "constant-arrival-rate",
      exec: "keyspaceWalk",
      rate: RATE,
      timeUnit: "1s",
      duration: DURATION,
      preAllocatedVUs: Math.max(10, RATE),
      maxVUs: Math.max(30, RATE * 3),
    },
  },
};

const THRESHOLDS = {
  capacity: {
    // Abort as soon as the Pi is clearly past its useful range.
    http_req_failed: [{ threshold: "rate<0.02", abortOnFail: true }],
    http_req_duration: [{ threshold: "p(95)<2000", abortOnFail: true }],
  },
  default: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<800"],
    checks: ["rate>0.99"],
  },
};

export const options = {
  scenarios: SCENARIOS[PHASE] || SCENARIOS.steady,
  thresholds: PHASE === "capacity" ? THRESHOLDS.capacity : THRESHOLDS.default,
  // Percentiles only — min/max/avg/count duplicate the console summary and
  // double the Prometheus series count.
  summaryTrendStats: ["min", "med", "p(90)", "p(95)", "p(99)", "max"],
};

// ---------------------------------------------------------------- exec fns

// Representative mix: HTML list/grid/detail plus the API surface.
export function mixedTraffic(data) {
  const r = Math.random();
  if (r < 0.3) {
    record(getGrid(1 + Math.floor(Math.random() * 3)), "htmx_product_grid");
  } else if (r < 0.5) {
    record(getList(1 + Math.floor(Math.random() * 3)), "html_product_list");
  } else if (r < 0.7) {
    record(getApiList(1 + Math.floor(Math.random() * 3)), "api_product_list");
  } else if (r < 0.9) {
    const slug = data.slugs[Math.floor(Math.random() * Math.min(10, data.slugs.length))];
    record(getApiDetail(slug), "api_product_detail");
  } else {
    const slug = data.slugs[Math.floor(Math.random() * Math.min(10, data.slugs.length))];
    record(getDetail(slug), "html_product_detail");
  }
  sleep(0.2);
}

// Miss cost vs hit cost, per endpoint, with no concurrency to confound it.
// Assumes the cache was flushed immediately before this run.
export function coldWarmProbe(data) {
  const probes = [
    { name: "html_product_list", fn: () => getList(1) },
    { name: "htmx_product_grid", fn: () => getGrid(1) },
    { name: "api_product_list", fn: () => getApiList(1) },
    { name: "html_product_detail", fn: () => getDetail(data.slugs[0]) },
    { name: "api_product_detail", fn: () => getApiDetail(data.slugs[0]) },
  ];

  // Pass 1 — cold. Every key should report MISS.
  for (const p of probes) {
    const res = p.fn();
    const state = record(res, p.name);
    check(res, {
      "cold: status 200": (r) => r.status === 200,
      "cold: reported MISS": () => state === "MISS",
    });
    console.log(`COLD  ${p.name.padEnd(22)} ${state.padEnd(7)} ${res.timings.duration.toFixed(1)}ms`);
    sleep(0.5);
  }

  // Pass 2 — warm. Same keys, well inside every TTL.
  for (const p of probes) {
    const res = p.fn();
    const state = record(res, p.name);
    check(res, {
      "warm: status 200": (r) => r.status === 200,
      "warm: reported HIT": () => state === "HIT",
    });
    console.log(`WARM  ${p.name.padEnd(22)} ${state.padEnd(7)} ${res.timings.duration.toFixed(1)}ms`);
    sleep(0.5);
  }
}

export function warmTarget() {
  const res = hitTarget();
  const state = record(res, TARGET_ENDPOINT);
  console.log(`WARM target=${TARGET} state=${state} ${res.timings.duration.toFixed(1)}ms`);
  check(res, { "warm: status 200": (r) => r.status === 200 });
}

// All BURST_VUS VUs arrive together just after expiry. The MISS count for this
// burst is the number of recomputations — the whole point of the exercise.
export function burstTarget() {
  const res = hitTarget();
  const state = record(res, TARGET_ENDPOINT);
  check(res, {
    "burst: status 200": (r) => r.status === 200,
    "burst: cache state known": () => state !== "UNKNOWN",
  });
}

// Variant-aware keys: the HTMX fragment and the full page share a path and a
// querystring, and must not share a cache entry.
export function variantProbe() {
  const full = http.get(`${BASE_URL}/products/?page=1`, {
    tags: { name: "variant_full" },
  });
  check(full, {
    "full page returns html shell": (r) => r.body && r.body.includes("<html"),
    "full page status 200": (r) => r.status === 200,
  });

  const frag = http.get(`${BASE_URL}/products/grid/?page=1`, {
    headers: { "HX-Request": "true" },
    tags: { name: "variant_fragment" },
  });
  check(frag, {
    "fragment omits html shell": (r) => r.body && !r.body.includes("<html"),
    "fragment contains grid markup": (r) =>
      r.body && (r.body.includes("product-grid") || r.body.includes("product-card")),
    "fragment status 200": (r) => r.status === 200,
  });

  sleep(0.5);
}

// Working set far larger than the hot set: every page, every slug, uniformly.
// Drives memcached_current_items up and exposes eviction behaviour.
export function keyspaceWalk(data) {
  const r = Math.random();
  if (r < 0.4) {
    record(getGrid(1 + Math.floor(Math.random() * 7)), "htmx_product_grid");
  } else if (r < 0.6) {
    record(getList(1 + Math.floor(Math.random() * 7)), "html_product_list");
  } else {
    const slug = data.slugs[Math.floor(Math.random() * data.slugs.length)];
    record(r < 0.8 ? getApiDetail(slug) : getDetail(slug),
           r < 0.8 ? "api_product_detail" : "html_product_detail");
  }
  sleep(0.2);
}

export function teardown() {
  console.log(`PHASE=${PHASE} complete.`);
}
