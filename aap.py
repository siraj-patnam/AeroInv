import streamlit as st
import mysql.connector
from mysql.connector import Error

def test_database_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="sirajfaraz",  # Use the password you just set
            database="aircraftmaintenancedb"
        )
        
        if connection.is_connected():
            db_info = connection.get_server_info()
            st.success(f"Successfully connected to MySQL Server version {db_info}")
            
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE();")
            db_name = cursor.fetchone()
            st.success(f"Connected to database: {db_name[0] if db_name else 'Unknown'}")
            
            # Test a simple query
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()
            st.write("Tables in the database:")
            for table in tables:
                st.write(table[0])
            
            cursor.close()
            connection.close()
            return True
        else:
            st.error("Failed to connect to the database")
            return False
    except Error as e:
        st.error(f"Connection error: {e}")
        return False

# Add this to your Streamlit app
if st.button("Test Database Connection"):
    test_database_connection()