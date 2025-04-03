# Database connection function
from shared_imports import *

def init_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="sirajfaraz",  # Replace with your actual password
            database="aircraftmaintenancedb"
        )
        return connection
    except Error as e:
        st.error(f"Error connecting to MySQL Database: {e}")
        return None

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