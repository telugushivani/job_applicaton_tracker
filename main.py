
from fastapi import FastAPI, HTTPException, Query,Depends
from datetime import date

from security import hash_password, verify_password, create_access_token, verify_access_token

from schema import JobApplication, JobApplicationUpdate,UserRegister,UserLogin
from database import connection
from config import JWT_SECRET_KEY, JWT_ALGORITHM
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

app = FastAPI(title="Job Application Tracker API")


bearer_scheme = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    token = credentials.credentials

    payload = verify_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return int(payload["sub"])

# User registration
@app.post("/register")
def register_user(user: UserRegister):
    hashed_password = hash_password(user.password)

    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO users (name, email, password_hash)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (user.name, user.email, hashed_password)
        )

        user_id = cursor.fetchone()[0]
        connection.commit()

        return {
            "message": "User registered successfully",
            "user_id": user_id
        }

    except Exception as error:
        connection.rollback()

        if getattr(error, "sqlstate", None) == "23505":
            raise HTTPException(
                status_code=409,
                detail="Email already registered"
            )

        raise

    finally:
        cursor.close()


# User login
@app.post("/login")
def login_user(user: UserLogin):
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT id, password_hash
            FROM users
            WHERE email = %s
            """,
            (user.email,)
        )

        existing_user = cursor.fetchone()

        if existing_user is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        user_id, hashed_password = existing_user

        if not verify_password(user.password, hashed_password):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        access_token = create_access_token(user_id)

        return {
            "message": "Login successful",
            "access_token": access_token,
            "token_type": "bearer"
        }

    finally:
        cursor.close()
        



# 1. Home endpoint
@app.get("/")
def job_application():
    return {
        "message": "Job Application Tracker API"
    }


# 2. Create a new application
@app.post("/applications")
def create_application(application: JobApplication,
                       current_user: int = Depends(get_current_user)):
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO applications
            (
                company, job_role, location, employment_type,
                source, salary_min, salary_max, application_date,
                status, job_url
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                application.company,
                application.job_role,
                application.location,
                application.employment_type,
                application.source,
                application.salary_min,
                application.salary_max,
                application.application_date,
                application.status,
                application.job_url
            )
        )

        application_id = cursor.fetchone()[0]
        connection.commit()

        return {
            "message": "Application created successfully",
            "application_id": application_id
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()


# 3. Get applications with filters, sorting and pagination
@app.get("/applications")
def get_applications(
    
    status: str | None = None,
    employment_type: str | None = None,
    min_salary: int | None = None,
    max_salary: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    sort_by: str = Query(default="application_date"),
    sort_order: str = Query(default="desc"),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: int = Depends(get_current_user)
):
    if (
        start_date is not None
        and end_date is not None
        and start_date > end_date
    ):
        raise HTTPException(
            status_code=400,
            detail="Start date cannot be after end date"
        )

    allowed_sort_fields = {
        "application_date": "application_date",
        "salary_min": "salary_min",
        "salary_max": "salary_max",
        "company": "company"
    }

    if sort_by not in allowed_sort_fields:
        raise HTTPException(
            status_code=400,
            detail="Invalid sort field"
        )

    if sort_order.lower() not in ("asc", "desc"):
        raise HTTPException(
            status_code=400,
            detail="Sort order must be asc or desc"
        )

    cursor = connection.cursor()

    try:
        query = "SELECT * FROM applications WHERE 1=1"
        values = []

        if status:
            query += " AND status = %s"
            values.append(status)

        if employment_type:
            query += " AND employment_type = %s"
            values.append(employment_type)

        if min_salary is not None:
            query += " AND salary_min >= %s"
            values.append(min_salary)

        if max_salary is not None:
            query += " AND salary_max <= %s"
            values.append(max_salary)

        if start_date is not None:
            query += " AND application_date >= %s"
            values.append(start_date)

        if end_date is not None:
            query += " AND application_date <= %s"
            values.append(end_date)

        # Count all matching records before pagination
        count_query = query.replace(
            "SELECT *",
            "SELECT COUNT(*)",
            1
        )

        cursor.execute(count_query, tuple(values))
        total = cursor.fetchone()[0]

        # Sorting
        query += (
            f" ORDER BY {allowed_sort_fields[sort_by]} "
            f"{sort_order.upper()}"
        )
        query += ", id DESC LIMIT %s OFFSET %s"

        # Pagination
        values.extend([limit, offset])

        cursor.execute(query, tuple(values))
        applications = cursor.fetchall()

        return {
            "total_applications": total,
            "limit": limit,
            "offset": offset,
            "applications": applications
        }

    finally:
        cursor.close()


# 4. Search applications by company name
@app.get("/applications/search")
def search_applications(company: str):
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT * FROM applications
            WHERE company ILIKE %s
            ORDER BY application_date DESC
            """,
            ("%" + company + "%",)
        )

        return cursor.fetchall()

    finally:
        cursor.close()


# 5. Total number of applications
@app.get("/applications/summary")
def applications_summary(current_user: int = Depends(get_current_user)):
    cursor = connection.cursor()

    try:
        cursor.execute(
            "SELECT COUNT(*) FROM applications"
        )

        total = cursor.fetchone()[0]

        return {
            "total_applications": total
        }

    finally:
        cursor.close()


# 6. Count applications by status
@app.get("/applications/summary/status")
def applications_summary_by_status(current_user: int = Depends(get_current_user)):
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT status, COUNT(*)
            FROM applications
            GROUP BY status
            ORDER BY status
            """
        )

        results = cursor.fetchall()

        return {
            "applications_by_status": results
        }

    finally:
        cursor.close()


# 7. Count applications by employment type
@app.get("/applications/summary/employment-type")
def applications_summary_by_employment_type(current_user: int = Depends(get_current_user)):
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT employment_type, COUNT(*)
            FROM applications
            GROUP BY employment_type
            ORDER BY employment_type
            """
        )

        results = cursor.fetchall()

        return {
            "applications_by_employment_type": results
        }

    finally:
        cursor.close()


# 8. Salary statistics
@app.get("/applications/summary/salary")
def salary_summary():
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT
                MIN(salary_min),
                MAX(salary_max),
                AVG(salary_min),
                AVG(salary_max)
            FROM applications
            """
        )

        result = cursor.fetchone()

        return {
            "minimum_salary": result[0],
            "maximum_salary": result[1],
            "average_minimum_salary": result[2],
            "average_maximum_salary": result[3]
        }

    finally:
        cursor.close()


# 9. Count applications by company
@app.get("/applications/summary/company")
def applications_summary_by_company(current_user: int = Depends(get_current_user)):
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT company, COUNT(*)
            FROM applications
            GROUP BY company
            ORDER BY COUNT(*) DESC
            """
        )

        results = cursor.fetchall()

        return {
            "applications_by_company": results
        }

    finally:
        cursor.close()


# 10. Count applications by month
@app.get("/applications/summary/month")
def applications_summary_by_month(current_user: int = Depends(get_current_user)):
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT
                TO_CHAR(application_date, 'YYYY-MM') AS month,
                COUNT(*) AS total_applications
            FROM applications
            GROUP BY TO_CHAR(application_date, 'YYYY-MM')
            ORDER BY month
            """
        )

        results = cursor.fetchall()

        return {
            "applications_by_month": [
                {
                    "month": row[0],
                    "total_applications": row[1]
                }
                for row in results
            ]
        }

    finally:
        cursor.close()


# 11. Get one application by ID
@app.get("/applications/{id}")
def replace_application(
    id: int,
    application: JobApplication,
    current_user: int = Depends(get_current_user)
):
    cursor = connection.cursor()

    try:
        cursor.execute(
            "SELECT * FROM applications WHERE id = %s",
            (id,)
        )

        application = cursor.fetchone()

        if application is None:
            raise HTTPException(
                status_code=404,
                detail="Application not found"
            )

        return application

    finally:
        cursor.close()


# 12. Replace all application fields (PUT)
@app.put("/applications/{id}")
def replace_application(
    id: int,
    application: JobApplication,
    current_user: int = Depends(get_current_user)
):
    cursor = connection.cursor()

    try:
        if application.salary_min > application.salary_max:
            raise HTTPException(
                status_code=400,
                detail="Minimum salary cannot exceed maximum salary"
            )

        cursor.execute(
            """
            UPDATE applications
            SET company = %s,
                job_role = %s,
                location = %s,
                employment_type = %s,
                source = %s,
                salary_min = %s,
                salary_max = %s,
                application_date = %s,
                status = %s,
                job_url = %s
            WHERE id = %s
            """,
            (
                application.company,
                application.job_role,
                application.location,
                application.employment_type,
                application.source,
                application.salary_min,
                application.salary_max,
                application.application_date,
                application.status,
                application.job_url,
                id
            )
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Application not found"
            )

        connection.commit()

        return {
            "message": "Application replaced successfully",
            "application_id": id
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()


# 13. Update only provided fields (PATCH)
@app.patch("/applications/{id}")
def update_application(
    id: int,
    application: JobApplicationUpdate,
    current_user: int = Depends(get_current_user)
):
    updates = application.model_dump(exclude_unset=True)

    if not updates:
        raise HTTPException(
            status_code=400,
            detail="No fields provided to update"
        )

    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT salary_min, salary_max
            FROM applications
            WHERE id = %s
            """,
            (id,)
        )

        existing = cursor.fetchone()

        if existing is None:
            raise HTTPException(
                status_code=404,
                detail="Application not found"
            )

        salary_min = updates.get("salary_min", existing[0])
        salary_max = updates.get("salary_max", existing[1])

        if salary_min > salary_max:
            raise HTTPException(
                status_code=400,
                detail="Minimum salary cannot exceed maximum salary"
            )

        set_clause = ", ".join(
            f"{key} = %s" for key in updates
        )

        values = list(updates.values())
        values.append(id)

        query = f"""
            UPDATE applications
            SET {set_clause}
            WHERE id = %s
        """

        cursor.execute(query, tuple(values))
        connection.commit()

        return {
            "message": "Application updated successfully",
            "application_id": id
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()


# 14. Delete an application
@app.delete("/applications/{id}")
def delete_application(id: int,
                        current_user: int = Depends(get_current_user)):
    cursor = connection.cursor()

    try:
        cursor.execute(
            "DELETE FROM applications WHERE id = %s",
            (id,)
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Application not found"
            )

        connection.commit()

        return {
            "message": "Application deleted successfully",
            "application_id": id
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
