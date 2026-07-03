# -*- coding: utf-8 -*-
"""
קובץ: db.py
תיאור: ניהול החיבור למסד הנתונים PostgreSQL והרצת שאילתות DDL/DML.
"""

import psycopg2

# פרטי החיבור למסד הנתונים כפי שהוגדרו בדרישות
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "mydatabase",
    "user": "or",
    "password": "1234"
}

def get_connection():
    """
    יוצר ומחזיר חיבור חדש למסד הנתונים PostgreSQL.
    """
    return psycopg2.connect(**DB_CONFIG)

def execute_query(query, params=None):
    """
    מריץ שאילתה שאינה מחזירה שורות (כגון INSERT, UPDATE, DELETE, CALL).
    מבצע Commit אוטומטי במקרה של הצלחה, ו-Rollback במקרה של שגיאה.
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(query, params or ())
    finally:
        conn.close()

def fetch_query(query, params=None):
    """
    מריץ שאילתה שמחזירה שורות (כגון SELECT או פונקציות שמחזירות ערך)
    ומחזיר את כל התוצאות כרשימה של טאפלים.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            return cur.fetchall()
    finally:
        conn.close()

def fetch_columns(query, params=None):
    """
    מריץ שאילתה ומחזיר גם את התוצאות וגם את שמות העמודות.
    שימושי להצגת שאילתות דינמיות בטבלאות (Treeview).
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            return columns, rows
    finally:
        conn.close()
