# Django Systems Learning Lab 🧱🚀

*A reusable, foundational backend project designed to be iterated on and extended into future applications.*

## 🎯 Project Overview

A backend-first Django project built as a **systems learning lab**: the aim is to understand how modern web applications are structured, scaled, and tuned by building the infrastructure layer first (configuration, storage, caching, and delivery) before committing to heavy domain logic.

This repository prioritises:

* **Environment correctness** (clear separation of local/dev and future production settings)
* **Production-aligned infrastructure patterns** (object storage, caching, CDN concepts)
* **Performance awareness** (measuring and reducing bottlenecks as the stack evolves)

This project is **not a one-size-fits-all blueprint for system design**. Instead, it represents *one well-reasoned approach* based on the use cases being explored here. Real-world architectures vary depending on scale, domain, and constraints.

> **Note:** The application is intentionally light on “product features” at this stage. The value is in the architecture and the learning path.

---

## 💡 Example Use Cases

While this project is intentionally domain-agnostic, the architecture is designed to support several common real-world application patterns once feature logic is layered on.

Typical use cases include:

* SaaS platforms and dashboards
* Content-driven or educational platforms
* API-first backends / backend-for-frontend (BFF)
* Reusable internal platform foundations


These examples are illustrative rather than prescriptive. The architecture reflects one valid approach among many, chosen to explore scalability, performance, and system design trade-offs in a realistic context.

---

## 🧭 Project Phases

This project is developed in **explicit phases**, each introducing a specific backend/infrastructure concern. Phases are additive: once introduced, components remain part of the system unless intentionally refactored.

### Phase 1: Foundational Backend & Configuration *(Complete ✅)*

This phase established the foundation of the Django project, including environment configuration, initial app structure, and baseline dependencies. The goal was to create a clean, modular framework that supports scaling into containerization, database integration, and future feature phases.

### Phase 2: Docker PostgreSQL Setup *(Complete ✅)*

This phase introduced the migration from SQLite to a containerized PostgreSQL database using Docker.
The main goals were stability, scalability, and environment consistency between local and production setup for realistic persistence, schema evolution, and production-aligned behaviour replacing the default SQLite database. 

### Phase 3: MinIO Docker Integration (Testing) + Lightweight Frontend UI Layer *(Complete ✅)*

This phase introduces object storage and CDN emulation for handling static and media files outside the Django container. The objective is to separate file storage from the core app via an S3-compatible object storage layer **for local/testing** to mimic production storage semantics. A lightweight UI exists primarily to validate asset delivery and API consumption.

### Phase 4: Redis via Docker + DRF Implementation for APIs *(In Progress 🚧)*

Introduces Redis to explore caching strategies and performance trade-offs. Expands API structure using Django REST Framework.

### Phase 5: Cloudflare CDN (Live) *(Planned ⏳)*

Adds a CDN layer intended for **live deployments** to explore edge caching, asset delivery, and cache invalidation at scale.

### 🔮 Future Phases (Planned)

More phases will be added as the system expands, including (but not limited to):

* Load balancing and reverse proxy strategies
* CI/CD pipelines and automated testing
* Performance benchmarking and profiling
* Staging/production environment parity
* Observability (logging/metrics/tracing)

---

## 🏗️ Stack & Architecture Overview

### Core stack

* **Backend:** Django + Django REST Framework (DRF)
* **Database:** PostgreSQL (Docker)
* **Caching / In-memory:** Redis (Docker)
* **Object storage (local/testing):** MinIO (Docker, S3-compatible)
* **CDN (live):** Cloudflare
* **Containerisation:** Docker / Docker Compose
* **Frontend:** Lightweight UI layer (primarily for validation, not feature depth)

### Component responsibilities

* **Django/DRF**: request handling, auth, API boundaries, business rules, integration glue
* **PostgreSQL**: durable persistence for core application data
* **Redis**: caching experiments to reduce repeated work and improve response times
* **MinIO (dev/testing)**: production-aligned object storage workflows (buckets, policies, asset URLs)
* **Cloudflare (live)**: edge caching and delivery layer for production performance

---

## ⚙️ Project Setup

> **Placeholder:** A full step-by-step setup guide will be added here.
>
> This project is designed to run locally using Docker and environment-specific settings. The development environment is working, while some Docker/deployment refinements are still being iterated on.

---

## 📍 Current State

* Infrastructure-first foundation is in place (settings isolation, PostgreSQL, MinIO-based object storage testing).
* The application is intentionally light on domain data and feature depth.
* APIs are introduced gradually as part of the learning and performance process.

---

## 🔭 Future Direction

The project will continue expanding into more production-grade concerns, including staging/production environments, load balancing, CI/CD, and structured performance testing.

---

## 👥 Intended Audience

This repository is for developers who want to understand backend architecture and system design by building and iterating on a production-aligned Django stack—rather than focusing purely on application features.
