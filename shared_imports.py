import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import time
import uuid
import base64
from PIL import Image
import io
import sys
import os


# Database connection function
@st.cache_resource
def init_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="sirajfaraZ5$",  # Replace with your actual password
        database="aircraft_maintenance_db"
    )

# Function to execute queries
@st.cache_data(ttl=600)
def run_query(query, params=None):
    conn = init_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        result = cursor.fetchall()
        conn.commit()
        return result
    except Exception as e:
        st.error(f"Query Error: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()

# Function to run insert/update/delete queries
def run_mutation(query, params=None):
    conn = init_connection()
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        st.error(f"Mutation Error: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()