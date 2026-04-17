"""
lib/db.py — Supabase connection and ALL CRUD functions for the lecture management app.
All pages import from lib.db.
"""

import streamlit as st
from supabase import create_client, Client


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

def get_client() -> Client:
    """Return a cached Supabase client stored in st.session_state."""
    if "supabase_client" not in st.session_state:
        url: str = st.secrets["SUPABASE_URL"]
        key: str = st.secrets["SUPABASE_KEY"]
        st.session_state["supabase_client"] = create_client(url, key)
    return st.session_state["supabase_client"]


# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------

def get_classes() -> list[dict]:
    client = get_client()
    response = client.table("classes").select("*").order("created_at").execute()
    return response.data


def create_class(name: str) -> dict:
    client = get_client()
    response = client.table("classes").insert({"name": name}).execute()
    return response.data[0]


def update_class(class_id: int, name: str) -> dict:
    client = get_client()
    response = (
        client.table("classes")
        .update({"name": name})
        .eq("id", class_id)
        .execute()
    )
    return response.data[0]


def delete_class(class_id: int) -> None:
    client = get_client()
    client.table("classes").delete().eq("id", class_id).execute()


# ---------------------------------------------------------------------------
# Students
# ---------------------------------------------------------------------------

def get_students(class_id: int | None = None) -> list[dict]:
    """Return students joined with their class name.
    Optionally filter by class_id.
    """
    client = get_client()
    query = client.table("students").select("*, classes(name)").order("name")
    if class_id is not None:
        query = query.eq("class_id", class_id)
    response = query.execute()
    return response.data


def get_students_by_school() -> list[dict]:
    """Return all students ordered by school_name then name."""
    client = get_client()
    response = (
        client.table("students")
        .select("*, classes(name)")
        .order("school_name")
        .order("name")
        .execute()
    )
    return response.data


def create_student(class_id: int, name: str, school_name: str) -> dict:
    client = get_client()
    response = (
        client.table("students")
        .insert({"class_id": class_id, "name": name, "school_name": school_name})
        .execute()
    )
    return response.data[0]


def update_student(student_id: int, **fields) -> dict:
    """Update arbitrary fields on a student record."""
    client = get_client()
    response = (
        client.table("students")
        .update(fields)
        .eq("id", student_id)
        .execute()
    )
    return response.data[0]


def delete_student(student_id: int) -> None:
    client = get_client()
    client.table("students").delete().eq("id", student_id).execute()


def bulk_create_students(students: list[dict]) -> list[dict]:
    """Insert multiple students at once.

    Each dict must contain: class_id, name, school_name.
    """
    client = get_client()
    response = client.table("students").insert(students).execute()
    return response.data


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

def get_categories() -> list[dict]:
    client = get_client()
    response = (
        client.table("categories")
        .select("*")
        .order("sort_order")
        .execute()
    )
    return response.data


def create_category(name: str, sort_order: int) -> dict:
    client = get_client()
    response = (
        client.table("categories")
        .insert({"name": name, "sort_order": sort_order})
        .execute()
    )
    return response.data[0]


def update_category(category_id: int, **fields) -> dict:
    client = get_client()
    response = (
        client.table("categories")
        .update(fields)
        .eq("id", category_id)
        .execute()
    )
    return response.data[0]


def delete_category(category_id: int) -> None:
    client = get_client()
    client.table("categories").delete().eq("id", category_id).execute()


# ---------------------------------------------------------------------------
# Exams
# ---------------------------------------------------------------------------

def get_exams() -> list[dict]:
    client = get_client()
    response = (
        client.table("exams")
        .select("*")
        .order("exam_date", desc=True)
        .execute()
    )
    return response.data


def create_exam(name: str, exam_type: str, exam_date: str) -> dict:
    """Create an exam.

    exam_type must be one of: '중간', '기말', '모의고사'.
    exam_date should be an ISO date string, e.g. '2025-09-01'.
    """
    client = get_client()
    response = (
        client.table("exams")
        .insert({"name": name, "exam_type": exam_type, "exam_date": exam_date})
        .execute()
    )
    return response.data[0]


def delete_exam(exam_id: int) -> None:
    client = get_client()
    client.table("exams").delete().eq("id", exam_id).execute()


# ---------------------------------------------------------------------------
# Scores
# ---------------------------------------------------------------------------

def get_scores_by_exam(exam_id: int) -> list[dict]:
    client = get_client()
    response = (
        client.table("scores")
        .select("*")
        .eq("exam_id", exam_id)
        .execute()
    )
    return response.data


def get_scores_by_student(student_id: int) -> list[dict]:
    """Return all scores for a student, joined with exam details."""
    client = get_client()
    response = (
        client.table("scores")
        .select("*, exams(name, exam_type, exam_date)")
        .eq("student_id", student_id)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data


def upsert_score(
    student_id: int,
    exam_id: int,
    total_score: int,
    grade: int | None = None,
) -> dict:
    """Insert or update a score record (conflict on student_id + exam_id)."""
    client = get_client()
    payload: dict = {
        "student_id": student_id,
        "exam_id": exam_id,
        "total_score": total_score,
    }
    if grade is not None:
        payload["grade"] = grade
    response = (
        client.table("scores")
        .upsert(payload, on_conflict="student_id,exam_id")
        .execute()
    )
    return response.data[0]


# ---------------------------------------------------------------------------
# Category Scores
# ---------------------------------------------------------------------------

def get_category_scores(score_id: int) -> list[dict]:
    """Return category scores for a given score, joined with category names."""
    client = get_client()
    response = (
        client.table("category_scores")
        .select("*, categories(name)")
        .eq("score_id", score_id)
        .execute()
    )
    return response.data


def get_category_scores_by_student(student_id: int) -> list[dict]:
    """Return all category scores for a student via their scores."""
    client = get_client()
    response = (
        client.table("category_scores")
        .select("*, categories(name), scores!inner(student_id, exam_id)")
        .eq("scores.student_id", student_id)
        .execute()
    )
    return response.data


def upsert_category_score(score_id: int, category_id: int, score: int) -> dict:
    """Insert or update a category score (conflict on score_id + category_id)."""
    client = get_client()
    payload = {
        "score_id": score_id,
        "category_id": category_id,
        "score": score,
    }
    response = (
        client.table("category_scores")
        .upsert(payload, on_conflict="score_id,category_id")
        .execute()
    )
    return response.data[0]


# ---------------------------------------------------------------------------
# Consultations
# ---------------------------------------------------------------------------

def get_consultations_by_student(student_id: int) -> list[dict]:
    """Return all consultations for a student, joined with exam info, newest first."""
    client = get_client()
    response = (
        client.table("consultations")
        .select("*, exams(name, exam_type, exam_date)")
        .eq("student_id", student_id)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data


def create_consultation(
    student_id: int,
    exam_id: int,
    ai_draft: str,
    final_text: str = "",
) -> dict:
    client = get_client()
    response = (
        client.table("consultations")
        .insert(
            {
                "student_id": student_id,
                "exam_id": exam_id,
                "ai_draft": ai_draft,
                "final_text": final_text,
            }
        )
        .execute()
    )
    return response.data[0]


def update_consultation(consultation_id: int, final_text: str) -> dict:
    client = get_client()
    response = (
        client.table("consultations")
        .update({"final_text": final_text})
        .eq("id", consultation_id)
        .execute()
    )
    return response.data[0]


# ---------------------------------------------------------------------------
# Memos
# ---------------------------------------------------------------------------

def get_memos_by_student(student_id: int) -> list[dict]:
    client = get_client()
    response = (
        client.table("memos")
        .select("*")
        .eq("student_id", student_id)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data


def create_memo(student_id: int, content: str) -> dict:
    client = get_client()
    response = (
        client.table("memos")
        .insert({"student_id": student_id, "content": content})
        .execute()
    )
    return response.data[0]


def delete_memo(memo_id: int) -> None:
    client = get_client()
    client.table("memos").delete().eq("id", memo_id).execute()
