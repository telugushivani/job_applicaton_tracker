# job_applicaton_tracker

# Job Application Tracker API

A production-ready RESTful backend API built with **FastAPI**, **PostgreSQL** (using raw SQL via `psycopg2`), and **JWT Authentication**. This application enables users to manage job search activities, track application metrics, apply complex dynamic filtering, and inspect salary analytics.


## ✨ Key Features

- **🔐 Secure Authentication:** JWT bearer tokens with Argon2 password hashing using `pwdlib`.
- **📝 Complete CRUD Operations:** Create, retrieve, update (PUT/PATCH), and delete job application records.
- **🔍 Advanced Querying & Filtering:** Dynamic SQL filtering by status, employment type, salary threshold, and application date ranges.
- **📊 Analytics & Insights:** Real-time aggregated summaries including application counts by status, employment type, hiring company, monthly trends, and salary distributions.
- **⚡ Raw SQL Performance:** Direct PostgreSQL query handling with transaction management (`commit`/`rollback`).
- **🛡️ Schema Validation:** Request and response model validation using Pydantic v2.

---

## 🛠️ Tech Stack

- **Framework:** FastAPI
- **Database:** PostgreSQL
- **Database Driver:** `psycopg2` (Raw SQL queries)
- **Authentication & Security:** PyJWT, `pwdlib[argon2]`
- **Validation:** Pydantic v2
- **ASGI Server:** Uvicorn

---

# Project Structure

```text
job-application-tracker/
├── app/
│   ├── main.py        # FastAPI routes, middleware & business logic
│   ├── config.py      # Environment variables configuration
│   ├── database.py    # PostgreSQL connection setup
│   ├── schema.py      # Pydantic data schemas & validators
│   └── security.py    # JWT generation, token verification & password hashing
├── screenshots/       # Documentation screenshots
├── .env               # Local environment variables
└── README.md          # Project documentation
```

---

## 🗄️ Database Setup (PostgreSQL)

Create a local PostgreSQL database named `job_tracker` and set up the following schema:

```sql
CREATE DATABASE job_tracker;

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Applications table
CREATE TABLE applications (
    id SERIAL PRIMARY KEY,
    company VARCHAR(150) NOT NULL,
    job_role VARCHAR(150) NOT NULL,
    location VARCHAR(100) NOT NULL,
    employment_type VARCHAR(50) NOT NULL,
    source VARCHAR(100) NOT NULL,
    salary_min INT NOT NULL,
    salary_max INT NOT NULL,
    application_date DATE NOT NULL,
    status VARCHAR(50) NOT NULL,
    job_url TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- PostgreSQL server running locally

### 2. Clone the Repository
```bash
git clone https://github.com/your-username/job-application-tracker.git
cd job-application-tracker
```

### 3. Create and Activate Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install fastapi uvicorn psycopg2-binary python-dotenv pyjwt pwdlib[argon2]
```

### 5. Environment Configuration
Create a `.env` file in the project root directory and define your secret keys:

```env
JWT_SECRET_KEY=mzmyB89UNf2IXSvCgvrqZcCa87maQOCk4MCL-ozWkJ8
JWT_ALGORITHM=HS256
```

---

#  Running the Server

Start the Uvicorn development server:

```bash
python -m uvicorn app.main:app --reload
```

The server will spin up at `http://127.0.0.1:8000`.

---

##  API Documentation & Endpoints

Access the interactive Swagger UI documentation directly at:  
 **`http://127.0.0.1:8000/docs`**

### Key Endpoint Groups

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/register` | Register a new user 
| `POST` | `/login` | Authenticate user and receive JWT bearer token 
| `POST` | `/applications` | Submit a new job application record 
| `GET` | `/applications` | List applications with filters, sorting & pagination 
| `GET` | `/applications/search` | Search applications by company name 
| `GET` | `/applications/{id}` | Fetch detailed record for a specific application 
| `PUT` | `/applications/{id}` | Full replace update on an existing record 
| `PATCH` | `/applications/{id}` | Partial field update on an existing record 
| `DELETE` | `/applications/{id}` | Remove a job application record 
| `GET` | `/applications/summary` | Get total count of job applications 
| `GET` | `/applications/summary/status` | Aggregated count grouped by application status 
| `GET` | `/applications/summary/company` | Summary count grouped by target companies 
| `GET` | `/applications/summary/salary` | Min, Max, and Average salary metrics 
| `GET` | `/applications/summary/month` | Monthly application volume analytics 


### Application Search & Filters
![Filtered Search](./screenshots/04-filtered-search.png)
