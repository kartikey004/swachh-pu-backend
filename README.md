# Swachh PU Backend

Backend API for **Swachh PU Abhiyaan** — campus cleanliness task management system.

Built with **FastAPI** + **Supabase** (Auth, PostgreSQL, Storage).

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/kartikey004/swachh-pu-backend.git
cd swachh-pu-backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate    # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Supabase

1. Go to [supabase.com](https://supabase.com) → Create a new project
2. Go to **Settings → API** and copy your keys
3. Create `.env` file from template:

```bash
copy .env.example .env
```

4. Fill in your Supabase credentials in `.env`:

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

### 3. Setup Database

1. Go to Supabase Dashboard → **SQL Editor**
2. Copy and run the contents of `supabase/schema.sql`
3. This creates all tables, indexes, RLS policies, and storage buckets

### 4. Run the Server

```bash
uvicorn app.main:app --reload
```

Server runs at: **http://localhost:8000**

---

## 📖 API Documentation

Once the server is running, visit:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 📡 API Endpoints

### Auth
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/auth/signup` | Register new user | ❌ |
| POST | `/auth/login` | Login | ❌ |
| POST | `/auth/logout` | Logout | ✅ |
| GET | `/auth/me` | Get current user | ✅ |

### Profiles
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/profiles/me` | Get own profile | ✅ |
| PUT | `/profiles/me` | Update own profile | ✅ |
| GET | `/profiles/workers` | List workers | ✅ Admin |
| GET | `/profiles/{id}` | Get any profile | ✅ Admin |

### Tasks
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/tasks/` | Create task | ✅ |
| GET | `/tasks/` | List tasks (filtered) | ✅ |
| GET | `/tasks/my-tasks` | Worker's assigned tasks | ✅ Worker |
| GET | `/tasks/{id}` | Get task detail | ✅ |
| PATCH | `/tasks/{id}/assign` | Assign to worker | ✅ Admin |
| PATCH | `/tasks/{id}/reject` | Reject task | ✅ Admin |
| PATCH | `/tasks/{id}/complete` | Complete task | ✅ Worker |

### Upload
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/upload/photo` | Upload photo | ✅ |
| POST | `/upload/audio` | Upload audio | ✅ |

---

## 🗄️ Database Schema

| Table | Description |
|-------|-------------|
| `profiles` | Base user profile (name, role, phone) |
| `student_profiles` | Student details (roll_no, address, hostel) |
| `worker_profiles` | Worker details (employee_id, zone) |
| `tasks` | Task/complaint (photo, location, status, assigned_to) |

### Task Status Flow

```
pending → assigned → completed
pending → rejected
```

---

## 🏗️ Project Structure

```
app/
├── main.py              # FastAPI entry point
├── config.py            # Environment config
├── dependencies.py      # Auth middleware
├── models/              # Pydantic schemas
│   ├── auth.py
│   ├── profile.py
│   └── task.py
├── routers/             # API endpoints
│   ├── auth.py
│   ├── profiles.py
│   ├── tasks.py
│   └── upload.py
├── services/            # Supabase query logic
│   ├── auth_service.py
│   ├── profile_service.py
│   ├── task_service.py
│   └── storage_service.py
└── utils/
    └── supabase_client.py
```

---

## 🔑 Roles

| Role | Can Do |
|------|--------|
| **Student** | Create tasks, view own tasks |
| **Worker** | View assigned tasks, mark complete |
| **Admin** | View all tasks, assign, reject |
