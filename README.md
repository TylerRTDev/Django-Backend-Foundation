# Django Foundation: Custom Users, Profiles, and API Layer

A foundational Django project designed to be a **reusable backend scaffold** for future applications. This setup provides a secure, modular structure that can be extended with new features while maintaining clean separation between authentication, profile management, and data access through APIs.

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

## 📘 Phase 2: Modular Settings and Environment Isolation

### Key Enhancements

* Introduced modular settings system (`base/dev/prod`).
* Fixed `BASE_DIR` path resolution to project root.
* Added `DJANGO_SETTINGS_MODULE` to `.env`.
* Confirmed correct database file placement and migrations.
* Created standalone troubleshooting guide for configuration imports.

### Benefits

* Cleaner environment handling (no more mixed settings).
* Stable database and file path behavior.
* Ready for Docker integration and PostgreSQL migration in Phase 3.

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
SECRET_KEY=dev-dont-use-in-prod
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
DJANGO_SETTINGS_MODULE=config.settings.dev
```

---

## 🔮 Next Steps (Phase 3 Preview)

* Add Docker Compose for PostgreSQL.
* Introduce Whitenoise and Cloudflare CDN integration.
* Extend DRF for profile editing endpoints.
* Add modular production security settings.

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
