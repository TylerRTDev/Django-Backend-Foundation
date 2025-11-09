# Django Foundation: Custom Users, Profiles, and API Layer

A foundational Django project designed to be a **reusable backend scaffold** for future applications. This setup provides a secure, modular structure that can be extended with new features while maintaining clean separation between authentication, profile management, and data access through APIs.

> ⚠️ **Work in Progress**
>
> This project is currently undergoing active development.  
> Features, configuration files, and environment variables may change as the CDN and deployment phases are finalized.  
> Documentation is being updated alongside implementation to ensure accuracy.  
> Expect minor adjustments to settings, Docker configuration, and environment variables until Phase 3.5 (Cloudflare R2) is complete.

---

## 🎯 Project Overview

The goal of this project is to build a **strong Django backend foundation** with a maintainable structure that can support multiple projects over time. The design emphasizes:

* **Scalability** – easily add apps or services as your project grows.
* **Security** – custom authentication and profile management from day one.
* **Reusability** – minimal configuration required to repurpose this setup for new projects.
* **Extensibility** – designed for later integration with PostgreSQL, Whitenoise/Cloudflare, and split settings for production environments.

This foundation allows you to experiment, learn, and expand without redoing boilerplate work every time.

---

## ⚙️ Core Features and Concepts

### 1. Custom User Model

Django’s default `User` model uses a username for authentication, which can be restrictive. In this foundation, we replace it with a **custom User model** that uses an email address for login.

**Benefits:**

* Enables **email-based authentication** out of the box.
* Future-proofs your app — changing the user model later is painful.
* Allows adding extra fields (e.g., verification status, roles, or permissions) as needed.

### 2. Profile Model

Each user automatically gets a **Profile** via a one-to-one relationship with the User model. The Profile contains user-editable data such as `display_name`, `bio`, `timezone`, `language`, and optional avatar/social fields.

**Benefits:**

* Keeps authentication data (email, permissions) **separate** from personal or public-facing data.
* Lets you expand user information without cluttering the User model.
* The separation also aligns with clean database normalization practices.

### 3. Auto Profile Creation via Signals

A `post_save` signal listens for new user creation events and automatically generates a matching Profile.

**Benefits:**

* Prevents null or missing profiles.
* Ensures that any new user (via admin, registration form, or script) is fully linked to a Profile.

### 4. Admin Customization

The Django Admin interface has been enhanced to display Profile fields inline when editing a User.

**Benefits:**

* Simplifies administration — you can view and edit both User and Profile info in one place.
* Cleaner, more intuitive workflow for site admins.

### 5. Environment-Based Settings

We use the **`django-environ`** package to manage environment variables from a `.env` file.

**Benefits:**

* Keeps sensitive data (like `SECRET_KEY`) out of version control.
* Allows you to easily toggle between environments (development, staging, production) without changing the codebase.
* Follows the **12-factor app** principles for clean configuration management.

Example `.env` variables:

```bash
SECRET_KEY=dev-dont-use-in-prod
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
DJANGO_SETTINGS_MODULE=config.settings.dev
```

### 6. Static and Media Files (Current Setup)

Currently, static and media files are handled by Django’s default configuration using SQLite and `DEBUG=True` mode.

**Benefits:**

* Simple for local development.
* No additional configuration needed for now.

Later, these will be served more efficiently using **Whitenoise** (application-level static file serving) or **Cloudflare CDN** (edge-level caching). In production, **you only need one**—Cloudflare will be the external CDN layer, while Whitenoise can serve as a fallback or local solution.

---

## 🧠 API Layer — `/api/me/`

The API layer uses **Django REST Framework (DRF)** to provide a small, secure JSON-based endpoint that exposes the currently authenticated user and their profile.

### Why This Matters

Even though this project currently uses server-rendered templates, the API layer is what bridges Django’s backend with modern front-end frameworks (React, Vue, mobile apps) or even simple JavaScript widgets.

### Endpoint: `/api/me/`

When a logged-in user sends a GET request to `/api/me/`, the API returns a JSON representation of their user and profile data.

**Example Response:**

```json
[
  {
    "id": 1,
    "email": "example@email.com",
    "first_name": "Tyler",
    "last_name": "Dev",
    "is_verified": false,
    "profile": {
      "display_name": "Tyler RT",
      "bio": "Building cool stuff",
      "timezone": "Europe/London",
      "language": "en",
      "avatar": null,
      "preferences": {}
    }
  }
]
```

### How It Works

* **Serializer Layer:** Converts `User` and `Profile` model data into JSON.
* **ViewSet (`MeViewSet`):** Limits visibility to the authenticated user (`request.user`).
* **Router Registration:** Maps `/api/me/` to the `MeViewSet` automatically.

### Benefits of Having an API

* **Dynamic UI updates:** Fetch user data (e.g., username, avatar, progress) without a page reload.
* **Front-end integration:** Connect easily with React/Vue front-ends or mobile apps.
* **Future-proof:** The same API can power any interface — web, app, or third-party service.
* **Security:** Only the authenticated user can access their own data.

### Example Use Case — Profile Card

```javascript
fetch('/api/me/', { credentials: 'include' })
  .then(res => res.json())
  .then(([me]) => {
    document.querySelector('#avatar').src = me.profile.avatar || '/static/default.png';
    document.querySelector('#username').textContent = me.profile.display_name || me.email;
    document.querySelector('#bio').textContent = me.profile.bio || 'No bio yet.';
  });
```

This snippet can dynamically load a logged-in user’s name and bio into a page element — great for dashboards or sidebars.

---

## 🧪 Testing Setup

Testing is done using **pytest** and **pytest-django**.

* `pytest.ini` ensures Django’s settings are automatically configured.
* A basic test confirms that creating a User automatically creates a Profile.

**Benefits:**

* Faster, more readable tests compared to Django’s built-in test runner.
* Keeps your codebase reliable as you expand.

Command:

```bash
pytest -q
```

---

## 🏗️ Project Setup Summary

1. **Environment variables** control sensitive settings.
2. **SQLite** is used for local development (PostgreSQL will replace this later).
3. **Custom User & Profile models** form the base of all future user-related features.
4. **Admin site** provides one-stop management for users and profiles.
5. **API layer** allows JSON access to the current user (for web or mobile clients).
6. **pytest** ensures everything works as expected.

---

## 🚀 Phase 1 – Initial Project Setup

This phase marked the creation of the Django project and the establishment of its fundamental structure.  
The objective was to get a functioning baseline environment that could later evolve into a modular, containerized system.

**Highlights:**
- Created the initial Django project and confirmed successful run of the default development server.
- Configured virtual environment for Python dependency isolation.
- Installed Django and supporting core packages via `pip`.
- Initialized Git repository and added `.gitignore` for virtual environment, migrations, and configuration files.
- Defined base app and templates to verify routing and rendering.
- Verified admin site accessibility and default SQLite database migration.
- Added preliminary README outlining project purpose and roadmap.

**Outcome:**  
A working Django foundation was established — lightweight, single-settings, and fully local — ready to expand in Phase 2 into a modular configuration structure and, later, containerized infrastructure.

---

## 📘 Phase 2: Modular Settings and Environment Isolation

This phase established the foundation of the Django project, including environment configuration, initial app structure, and baseline dependencies.  
The goal was to create a clean, modular framework that supports scaling into containerization, database integration, and future feature phases.

**Highlights:**
- Initialized Django project with modular app architecture (`config/` and core apps directory).
- Created separate settings files (`base.py`, `dev.py`, and later `prod.py`) for environment-specific configuration.
- Configured virtual environment and initial dependency management (`requirements.txt`).
- Set up Git version control with appropriate `.gitignore` entries to exclude environment files and system artifacts.
- Verified successful local server startup (`python manage.py runserver`).
- Established basic app routing and `urls.py` structure for future expansion.
- Added README scaffold and documentation folder to track progressive development phases.

**Outcome:**  
Django was successfully initialized and fully operational in development mode, serving as the stable foundation for subsequent phases — including database integration, Dockerization, and CDN implementation.

### Benefits

* Cleaner environment handling (no more mixed settings).
* Stable database and file path behavior.
* Ready for Docker integration and PostgreSQL migration in Phase 3.

> 🗒️ **Side Note – Original Settings File**
>
> The original `settings.py` file created during project initialization has been preserved in the `config/` directory as a backup reference.  
> It is **not used for development or deployment**, as the project now follows a modular settings structure (`base.py`, `dev.py`, `prod.py`) introduced in Phase 2.  
> The backup remains available for historical context and rollback reference.

### Updated Project Structure

```text
project_root/
  manage.py
  config/
    __init__.py
    settings/
      __init__.py
      base.py
      dev.py
      prod.py
  accounts/
  static/
  media/
  .env
  .gitignore
  README.md
```

### Environment Variables Update

```dotenv
DJANGO_SECRET_KEY=dev-dont-use-in-prod
DJANGO_DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
DJANGO_SETTINGS_MODULE=config.settings.dev
```

---

### Phase 2.5 – PostgreSQL Database Integration
This phase introduced the migration from SQLite to a containerized PostgreSQL database using Docker.  
The main goals were stability, scalability, and environment consistency between local and production setups.

**Highlights:**
- Added PostgreSQL service to `docker-compose.yml` with persistent volume storage.
- Updated `config/settings/dev.py` to use PostgreSQL as the default backend.
- Configured environment variables through `.env` using `python-decouple`.
- Verified connectivity by running migrations, creating a superuser, and confirming data persistence across container restarts.
- Expanded documentation with database setup, Docker workflow, and health check commands.

This marks the completion of database containerization, ensuring all data operations now run against a production-grade system.

---

### ☁️ Phase 3 – CDN Implementation (MinIO)

This phase introduces **object storage and CDN emulation** for handling static and media files outside the Django container.  
The objective is to separate file storage from the core app while preparing the system for a future production-grade CDN.

**Highlights:**
- Integrated **MinIO** as a local, S3-compatible object storage service via Docker.
- Configured Django to use `django-storages` and the S3 API for file uploads.
- Updated environment variables to include MinIO credentials (`MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_BUCKET_NAME`, `MINIO_ENDPOINT_URL`).
- Verified full upload/download flow locally using the same API calls as Cloudflare R2.
- Implemented persistent Docker volume for local media file retention.
- Added documentation for MinIO container setup, credentials, and connection testing.

**Outcome:**  
Django now stores and retrieves files through MinIO using the same configuration pattern as production storage (S3 API).  
This creates a **zero-cost, offline-capable** development environment that mirrors real CDN behavior for testing.

---

### 🌐 Phase 3.5 – Cloudflare R2 Integration (Production CDN)

Building on the MinIO foundation, this phase migrates the storage backend to **Cloudflare R2**, providing global content delivery and scalability.

**Highlights:**
- Replaced MinIO credentials with Cloudflare R2 configuration:
  - `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`, `R2_ENDPOINT_URL`.
- Updated `config/settings/prod.py` to point to R2’s S3-compatible endpoint.
- Verified seamless transition by using the same `django-storages` interface.
- Configured `MEDIA_URL` to serve files through Cloudflare’s edge network for low-latency delivery.
- Documented environment setup, permissions, and R2 bucket management.
- Confirmed upload, retrieval, and cache-control behavior across global endpoints.

**Outcome:**  
The project now benefits from a **true CDN**, with globally distributed edge caching, zero egress costs, and no infrastructure maintenance.  
Cloudflare R2 delivers production-grade reliability and performance, completing the app’s scalable media-handling pipeline.

---

## 🧾 License

MIT — free to use, modify, and share.

---

## 🧭 Educational Takeaway

This project isn’t just a starting point — it’s a **learning scaffold** for Django fundamentals:

* How to correctly implement a custom user model.
* Why separating profile data is smart design.
* How to wire an API securely.
* How environment-based configuration supports scalable deployment.

Understanding these principles now will save massive time and headaches when projects grow from small experiments into full-scale applications.



