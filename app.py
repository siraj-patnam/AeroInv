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

# Add the current directory to the path so we can import the module files
sys.path.append(os.path.dirname(__file__))

# Import component modules
from pre_flight_analysis import pre_flight_analysis
from transfers_component import transfers 
from procurement_component import procurement
from compliance_component import compliance
from reports_component import reports, inventory_summary_report, part_usage_history_report
from reports_component import maintenance_requests_report, part_expiration_report
from reports_component import compliance_status_report, cost_analysis_report

# Required for styled sidebar menu
from streamlit_option_menu import option_menu

# Configure page settings
st.set_page_config(
    page_title="AeroInv - Aviation Parts Inventory System",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    .stButton button {
        width: 100%;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 1px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff;
        border-right: 1px solid #f0f2f6;
        border-left: 1px solid #f0f2f6;
        border-top: 2px solid #3498db;
    }
    div.stActionButton {
        visibility: hidden;
    }
</style>
""", unsafe_allow_html=True)

# Database connection function
@st.cache_resource
def init_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="sirajfaraZ5$",  # Replace with your MySQL password
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

# User authentication functions
def hash_password(password):
    # In production, use a more secure method
    return password  # For prototype only!

def verify_password(hashed_password, input_password):
    # In production, use a more secure method
    return hashed_password == input_password  # For prototype only!

def login():
    st.title("AeroInv - Aviation Parts Inventory System")
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if not username or not password:
                st.error("Please enter both username and password")
                return False
            
            # For prototype, hardcode some users
            # In a real app, this would query the database
            users = [
                {"user_id": 1, "username": "admin", "password": "admin123", "full_name": "Admin User", "role": "Administrator", "facility_id": 1},
                {"user_id": 2, "username": "technician", "password": "tech123", "full_name": "John Smith", "role": "Maintenance Technician", "facility_id": 2},
                {"user_id": 3, "username": "manager", "password": "manager123", "full_name": "Jane Doe", "role": "Operations Manager", "facility_id": 1}
            ]
            
            user = None
            for u in users:
                if u["username"] == username and verify_password(u["password"], password):
                    user = u
                    break
            
            if user:
                # Store user info in session state
                st.session_state.user = user
                st.session_state.logged_in = True
                st.success("Login successful!")
                time.sleep(1)  # Delay to show success message
                st.rerun()
                return True
            else:
                st.error("Invalid username or password")
                return False
                
    return False

# Sidebar navigation
def sidebar_navigation():
    with st.sidebar:
        st.title("AeroInv")
        
        selected = option_menu(
            "Main Menu",
            ["Dashboard", "Inventory", "Requests", "Transfers", 
             "Pre-Flight Analysis", "Procurement", "Compliance", "Reports"],
            icons=['house', 'box', 'list-check', 'arrow-left-right', 
                   'airplane', 'cart', 'clipboard-check', 'file-earmark-text'],
            menu_icon="gear",
            default_index=0
        )
        
        st.markdown("---")
        st.write(f"Logged in as: {st.session_state.user['full_name']}")
        st.write(f"Role: {st.session_state.user['role']}")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()
            
    return selected

# Dashboard
def dashboard():
    st.title("Dashboard")
    
    # Top row - Search and alerts
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.text_input("Search parts, requests, or orders...", placeholder="Enter keywords")
    
    # Create critical alerts
    critical_alerts = [
        {"id": 1, "message": "Hydraulic pump (P/N 45678) has 5 days until expiration"},
        {"id": 2, "message": "Low inventory alert: Fuel filters (P/N 12345) below threshold"}
    ]
    
    with col2:
        with st.expander("Critical Alerts", expanded=True):
            if critical_alerts and len(critical_alerts) > 0:
                for alert in critical_alerts:
                    st.warning(alert['message'])
            else:
                st.success("No critical alerts")
    
    # KPI metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Parts In Stock",
            value="1,247",
            delta="3% from last week"
        )
    
    with col2:
        st.metric(
            label="Open Requests",
            value="28",
            delta="-12% from last week",
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            label="Parts In Transit",
            value="43"
        )
        st.caption(f"Expected arrivals today: 17")
    
    with col4:
        st.metric(
            label="Upcoming Flights (24h)",
            value="12"
        )
        st.caption(f"Parts needed: 87")
    
    # Recent activity feed
    st.subheader("Recent Activity")
    
    recent_activity = [
        {"id": 1, "message": "John D. requested 3x AC Generator (10:45 AM)"},
        {"id": 2, "message": "Part Transfer #T2345 received at Hangar B (10:22 AM)"},
        {"id": 3, "message": "Maintenance scheduled for Flight FL-5678 (09:15 AM)"}
    ]
    
    if recent_activity and len(recent_activity) > 0:
        for activity in recent_activity:
            st.text(activity['message'])
    else:
        st.info("No recent activity")
    
    # Add charts to dashboard
    st.subheader("Inventory Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Mock data for inventory by category
        categories = ["Engine Components", "Avionics", "Landing Gear", "Interior", "Hydraulic", "Electrical"]
        counts = [450, 325, 175, 125, 100, 72]
        
        # Create pie chart
        fig1 = px.pie(
            values=counts,
            names=categories,
            title='Parts by Category'
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Mock data for inventory status
        status_labels = ["Good Stock", "Low Stock", "Out of Stock", "Expiring Soon"]
        status_counts = [1035, 125, 32, 55]
        status_colors = ['#4CAF50', '#FFC107', '#F44336', '#9C27B0']
        
        # Create pie chart
        fig2 = px.pie(
            values=status_counts,
            names=status_labels,
            title='Inventory Status',
            color_discrete_sequence=status_colors
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # Add trend chart
    st.subheader("Maintenance Request Trends")
    
    # Mock data for trends
    dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
    request_counts = [np.random.randint(5, 15) for _ in range(len(dates))]
    completion_counts = [max(0, count - np.random.randint(1, 5)) for count in request_counts]
    
    trend_data = pd.DataFrame({
        'date': dates,
        'requests': request_counts,
        'completions': completion_counts
    })
    
    # Create line chart
    fig3 = px.line(
        trend_data,
        x='date',
        y=['requests', 'completions'],
        title='Requests vs. Completions (30 Days)',
        labels={'value': 'Count', 'date': 'Date', 'variable': 'Type'},
        color_discrete_map={
            'requests': '#1976D2',
            'completions': '#4CAF50'
        }
    )
    st.plotly_chart(fig3, use_container_width=True)

# Inventory Management
def inventory_management():
    st.title("Inventory Management")
    
    # Make sure session state for selected part is initialized
    if 'selected_part_id' not in st.session_state:
        st.session_state.selected_part_id = None
    
    if 'add_part_modal' not in st.session_state:
        st.session_state.add_part_modal = False
    
    # Filtering options
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        search_term = st.text_input("Search parts...", key="inventory_search")
    
    with col2:
        categories = ["All", "Engine Components", "Avionics", "Landing Gear", "Interior", "Exterior", "Hydraulic", "Electrical", "Other"]
        category = st.selectbox("Category", options=categories)
    
    with col3:
        facilities = ["All", "ATL Maintenance Hangar", "BOS Service Center", "DEN Maintenance Hangar", "LAX Repair Facility"]
        facility = st.selectbox("Facility", options=facilities)
    
    with col4:
        if st.button("+ Add Part", type="primary"):
            st.session_state.add_part_modal = True
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Parts", "1,247")
    
    with col2:
        st.metric("Low Stock", "28")
    
    with col3:
        st.metric("Out of Stock", "16")
    
    with col4:
        st.metric("Expiring Soon", "12")
    
    # Mock data for inventory
    inventory_data = [
        {"part_id": 1, "part_number": "P-12345", "description": "Fuel Filter", "category": "Engine Components", 
         "in_stock": 4, "threshold": 10, "location": "Hangar A, Shelf B-124", "status": "LOW"},
        {"part_id": 2, "part_number": "P-45678", "description": "Hydraulic Pump", "category": "Hydraulic", 
         "in_stock": 8, "threshold": 5, "location": "Hangar B, Shelf A-3", "status": "GOOD"},
        {"part_id": 3, "part_number": "P-67890", "description": "Oil Separator", "category": "Engine Components", 
         "in_stock": 0, "threshold": 3, "location": "Hangar C, Shelf D-8", "status": "OUT"},
        {"part_id": 4, "part_number": "P-13579", "description": "Air Filter", "category": "Engine Components", 
         "in_stock": 15, "threshold": 8, "location": "Hangar A, Shelf C-22", "status": "GOOD"},
        {"part_id": 5, "part_number": "P-24680", "description": "Hydraulic Sensor", "category": "Hydraulic", 
         "in_stock": 6, "threshold": 4, "location": "Hangar D, Shelf E-15", "status": "GOOD"}
    ]
    
    # Filter mock data based on search and filters
    filtered_inventory = inventory_data
    
    if search_term:
        filtered_inventory = [item for item in filtered_inventory if 
                              search_term.lower() in item["part_number"].lower() or 
                              search_term.lower() in item["description"].lower()]
    
    if category != "All":
        filtered_inventory = [item for item in filtered_inventory if item["category"] == category]
    
    if facility != "All":
        # This is a simplified filter for the mock data
        filtered_inventory = [item for item in filtered_inventory if facility.split()[0] in item["location"]]
    
    # Convert filtered data to DataFrame
    if filtered_inventory:
        df = pd.DataFrame(filtered_inventory)
        
        # Add selection capability and display
        selected_rows = st.dataframe(
            df,
            column_config={
                "part_id": None,  # Hide column
                "part_number": "Part Number",
                "description": "Description",
                "category": "Category",
                "in_stock": "In Stock",
                "threshold": "Threshold",
                "location": "Location",
                "status": st.column_config.Column(
                    "Status",
                    help="Stock status based on threshold",
                    width="small"
                )
            },
            use_container_width=True,
            hide_index=True,
            selection="single"
        )
        
        # Handle row selection
        if selected_rows:
            selected_indices = selected_rows.get('selected_rows', [])
            if selected_indices:
                selected_index = selected_indices[0]
                st.session_state.selected_part_id = df.iloc[selected_index]["part_id"]
        
        # Part details (when clicking on a row)
        if st.session_state.selected_part_id:
            part_id = st.session_state.selected_part_id
            selected_part = next((p for p in inventory_data if p["part_id"] == part_id), None)
            
            if selected_part:
                with st.expander("Part Details", expanded=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader(f"{selected_part['part_number']}: {selected_part['description']}")
                        st.write(f"**Category:** {selected_part['category']}")
                        st.write(f"**Unit Cost:** $125.00")
                        st.write(f"**Shelf Life:** 24 months")
                        st.write(f"**Certification Status:** Certified")
                        st.write(f"**Document Reference:** MAN-ENG-123")
                    
                    with col2:
                        st.subheader("Inventory Actions")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Order Parts"):
                                st.success("Order created!")
                        
                        with col2:
                            if st.button("Transfer Parts"):
                                st.success("Transfer initiated!")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Update Quantity"):
                                st.success("Quantity updated!")
                        
                        with col2:
                            if st.button("View History"):
                                # Mock part history
                                part_history = [
                                    {"transaction_id": 1001, "transaction_type": "IN", "quantity": 10, "date": "2025-03-15", 
                                     "source": None, "destination": "ATL Maintenance Hangar", "user": "John Smith"},
                                    {"transaction_id": 1002, "transaction_type": "OUT", "quantity": 2, "date": "2025-03-18", 
                                     "source": "ATL Maintenance Hangar", "destination": None, "user": "Jane Doe"},
                                    {"transaction_id": 1003, "transaction_type": "OUT", "quantity": 2, "date": "2025-03-20", 
                                     "source": "ATL Maintenance Hangar", "destination": None, "user": "John Smith"},
                                    {"transaction_id": 1004, "transaction_type": "TRANSFER", "quantity": 4, "date": "2025-03-22", 
                                     "source": "ATL Maintenance Hangar", "destination": "LAX Repair Facility", "user": "Admin User"}
                                ]
                                
                                st.subheader("Part History")
                                history_df = pd.DataFrame(part_history)
                                st.dataframe(history_df, use_container_width=True, hide_index=True)
    else:
        st.info("No parts found matching your criteria")
    
    # Add Part Modal
    if st.session_state.get('add_part_modal', False):
        with st.form("add_part_form"):
            st.subheader("Add New Part")
            
            part_number = st.text_input("Part Number *")
            description = st.text_input("Description *")
            category = st.selectbox("Category *", options=["Engine Components", "Avionics", "Landing Gear", 
                                                          "Interior", "Exterior", "Hydraulic", "Electrical", "Other"])
            unit_cost = st.number_input("Unit Cost ($)", min_value=0.0, step=0.01)
            min_stock = st.number_input("Minimum Stock Level", min_value=0, step=1)
            expiration_date = st.date_input("Expiration Date (if applicable)", value=None)
            certification_status = st.selectbox("Certification Status", options=["Certified", "Pending", "Not Required"])
            document_reference = st.text_input("Document Reference (if applicable)")
            
            submit_col, cancel_col = st.columns(2)
            
            with submit_col:
                submit = st.form_submit_button("Save Part")
            
            with cancel_col:
                if st.form_submit_button("Cancel"):
                    st.session_state.add_part_modal = False
                    st.rerun()
            
            if submit:
                if not part_number or not description or not category:
                    st.error("Please fill in all required fields")
                else:
                    # In a real app, this would insert into database
                    st.success("Part added successfully!")
                    st.session_state.add_part_modal = False
                    time.sleep(1)
                    st.rerun()
# Initialize session state variables
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None

# Main app flow
if not st.session_state.get('logged_in', False):
    login()
else:
    # Navigation
    selection = sidebar_navigation()
    
    # Display the selected page
    if selection == "Dashboard":
        dashboard()
    elif selection == "Inventory":
        inventory_management()
    elif selection == "Pre-Flight Analysis":
        pre_flight_analysis()
    elif selection == "Transfers":
        transfers()
    elif selection == "Procurement":
        procurement()
    elif selection == "Compliance":
        compliance()
    elif selection == "Reports":
        reports()
    # Add handling for other pages if needed