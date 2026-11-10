"""
FastAPI Student Management System with PostgreSQL and SQLAlchemy ORM
====================================================================
This module replaces the static in-memory list (students = [...]) with a 
persistent PostgreSQL database using SQLAlchemy ORM and Pydantic validation.

Architecture Flow:
------------------
Client / Swagger UI (http://127.0.0.1:8000/docs)
       │
       ▼ (HTTP Requests: POST, GET, PUT, PATCH, DELETE)
FastAPI Application (Routing, Dependencies, Business Logic)
       │
       ▼ (Data Validation & Serialization)
Pydantic Schemas (StudentCreate, StudentUpdate, StudentResponse)
       │
       ▼ (Python Objects ↔ SQL Queries)
SQLAlchemy ORM (Engine, SessionLocal, Student Model)
       │
       ▼ (psycopg2-binary Driver)
PostgreSQL Database (student_db -> students table)
"""

import os
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from pydantic import BaseModel, ConfigDict


# ==============================================================================
# 1. DATABASE CONFIGURATION
# ==============================================================================
# Connection format: postgresql://username:password@host:port/database_name
# Note: With psycopg2-binary, SQLAlchemy uses the postgresql+psycopg2:// prefix.
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+psycopg2://postgres:Nazar123@localhost:5433/student_db"
)

# Normalize postgresql:// to postgresql+psycopg2:// if specified without driver
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

# create_engine: Manages the connection pool to PostgreSQL
engine = create_engine(DATABASE_URL)

# SessionLocal: Factory for creating new database sessions per request
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base: Declarative base class for SQLAlchemy models
Base = declarative_base()


# ==============================================================================
# 2. DATABASE MODEL (SQLAlchemy ORM)
# ==============================================================================
# Maps the Python class 'Student' to the PostgreSQL table 'students'
class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=True)
    email = Column(String(150), nullable=True)


# ==============================================================================
# 3. PYDANTIC SCHEMAS (Request & Response Validation)
# ==============================================================================
# Schema for creating a student (POST) and updating complete student (PUT)
class StudentCreate(BaseModel):
    name: str
    age: int
    email: str


# Schema for partially updating a student (PATCH)
class StudentUpdate(BaseModel):
    name: str | None = None
    age: int | None = None
    email: str | None = None


# Schema for returning student data in API responses
class StudentResponse(BaseModel):
    id: int
    name: str
    age: int | None = None
    email: str | None = None

    # Enable ORM mode to serialize SQLAlchemy models into Pydantic models
    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# 4. DATABASE SESSION DEPENDENCY
# ==============================================================================
def get_db():
    """
    Creates an independent database session for each incoming API request
    and ensures the session is properly closed when the request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==============================================================================
# 5. FASTAPI APPLICATION INITIALIZATION & TABLE CREATION
# ==============================================================================
app = FastAPI(
    title="Student Management API",
    description="FastAPI CRUD API with PostgreSQL & SQLAlchemy ORM",
    version="1.0.0"
)

# Automatically create database tables if they do not exist
# Note: Wrapped in try-except so the app can start even before PostgreSQL is configured
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Notice: Table creation deferred or PostgreSQL not reachable yet: {e}")


# ==============================================================================
# 6. API ENDPOINTS (FULL CRUD IMPLEMENTATION)
# ==============================================================================

@app.get("/")
def home():
    """Welcome route / health check"""
    return {
        "message": "Welcome to Student Management API with PostgreSQL & SQLAlchemy",
        "docs_url": "/docs"
    }


# ------------------------------------------------------------------------------
# 1. GET /students - Read all students
# ------------------------------------------------------------------------------
@app.get("/students", response_model=list[StudentResponse])
def get_students(db: Session = Depends(get_db)):
    """
    Retrieve all student records from PostgreSQL.
    Replaces: 'return students'
    """
    students = db.query(Student).all()
    return students


# ------------------------------------------------------------------------------
# 2. GET /students/{id} - Read a single student by ID
# ------------------------------------------------------------------------------
@app.get("/students/{id}", response_model=StudentResponse)
def get_student_by_id(id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific student by primary key ID.
    """
    student = db.query(Student).filter(Student.id == id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Student not found"
        )
    return student


# ------------------------------------------------------------------------------
# 3. POST /students - Create a new student
# ------------------------------------------------------------------------------
@app.post("/students", status_code=status.HTTP_201_CREATED)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    """
    Insert a new student into PostgreSQL.
    - db.add(): Stages the new object in session
    - db.commit(): Permanently saves the record into the database
    - db.refresh(): Reloads the object with DB-generated attributes (like ID)
    Replaces: 'students.append(student)'
    """
    new_student = Student(
        name=student.name,
        age=student.age,
        email=student.email
    )
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return {
        "message": "Student added successfully",
        "data": StudentResponse.model_validate(new_student)
    }


# ------------------------------------------------------------------------------
# 4. PUT /students/{id} - Update complete student details
# ------------------------------------------------------------------------------
@app.put("/students/{id}")
def update_student(id: int, student: StudentCreate, db: Session = Depends(get_db)):
    """
    Completely replace / update an existing student record.
    """
    existing_student = db.query(Student).filter(Student.id == id).first()
    if not existing_student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Student not found"
        )

    # Overwrite all fields
    existing_student.name = student.name
    existing_student.age = student.age
    existing_student.email = student.email

    db.commit()
    db.refresh(existing_student)
    return {
        "message": "Student updated successfully",
        "data": StudentResponse.model_validate(existing_student)
    }


# ------------------------------------------------------------------------------
# 5. PATCH /students/{id} - Partially update selected student fields
# ------------------------------------------------------------------------------
@app.patch("/students/{id}")
def patch_student(id: int, student: StudentUpdate, db: Session = Depends(get_db)):
    """
    Update only the fields provided in the request body.
    Replaces: 's.update(data)'
    """
    existing_student = db.query(Student).filter(Student.id == id).first()
    if not existing_student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Student not found"
        )

    # Extract only fields that were explicitly provided by the client
    update_data = student.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="No fields provided for update"
        )

    for key, value in update_data.items():
        setattr(existing_student, key, value)

    db.commit()
    db.refresh(existing_student)
    return {
        "message": "Student partially updated",
        "data": StudentResponse.model_validate(existing_student)
    }


# ------------------------------------------------------------------------------
# 6. DELETE /students/{id} - Remove student from database
# ------------------------------------------------------------------------------
@app.delete("/students/{id}")
def delete_student(id: int, db: Session = Depends(get_db)):
    """
    Delete a student record permanently from PostgreSQL.
    Replaces: 'students.remove(s)'
    """
    existing_student = db.query(Student).filter(Student.id == id).first()
    if not existing_student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Student not found"
        )

    db.delete(existing_student)
    db.commit()
    return {"message": "Student deleted successfully"}
