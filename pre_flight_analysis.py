# Pre-Flight Analysis
from shared_imports import *

def pre_flight_analysis():
    st.title("Pre-Flight Analysis")
    # Rest of your code
def pre_flight_analysis():
    st.title("Pre-Flight Analysis")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        date_ranges = ["Next 24 hours", "Next 48 hours", "Next 7 days"]
        date_range = st.selectbox("Date", options=date_ranges)
    
    with col2:
        # Get all facilities
        facilities = run_query("SELECT facility_id, facility_name FROM FACILITIES WHERE is_active = 1")
        facility_options = ["All"] + [f['facility_name'] for f in facilities]
        selected_facility = st.selectbox("Facility", options=facility_options)
    
    with col3:
        if st.button("Refresh"):
            st.experimental_rerun()
    
    # In a real application, this would query the Flight Schedule API
    # For prototype, use mock data
    flights = [
        {
            "flight_id": "FL-1234",
            "aircraft": "B737-800",
            "departure": "12:45 PM",
            "parts_needed": 5,
            "status": "ALERT"
        },
        {
            "flight_id": "FL-5678",
            "aircraft": "A320",
            "departure": "1:30 PM",
            "parts_needed": 3,
            "status": "PENDING"
        },
        {
            "flight_id": "FL-9012",
            "aircraft": "B787-9",
            "departure": "3:15 PM",
            "parts_needed": 7,
            "status": "READY"
        }
    ]
    
    # Display flights table
    st.subheader("Upcoming Flights")
    
    # Convert mock data to DataFrame
    flights_df = pd.DataFrame(flights)
    
    # Add status color
    def status_color(status):
        if status == "ALERT":
            return "background-color: #f8d7da"
        elif status == "PENDING":
            return "background-color: #fff3cd"
        else:
            return "background-color: #d1e7dd"
    
    # Display with styling
    st.dataframe(
        flights_df,
        column_config={
            "flight_id": "Flight",
            "aircraft": "Aircraft",
            "departure": "Departure",
            "parts_needed": "Parts Needed",
            "status": st.column_config.Column(
                "Status",
                width="small"
            )
        },
        use_container_width=True,
        hide_index=True
    )
    
    # Parts requirements for selected flight
    st.subheader("FL-1234 Parts Requirements")
    
    # Mock data for parts requirements
    parts_requirements = [
        {
            "part_number": "P-12345",
            "description": "Fuel Filter",
            "quantity": 2,
            "status": "Out of Stock"
        },
        {
            "part_number": "P-67890",
            "description": "Oil Separator",
            "quantity": 1,
            "status": "Low (2 left)"
        },
        {
            "part_number": "P-24680",
            "description": "Hydraulic Sensor",
            "quantity": 2,
            "status": "In Stock (15)"
        }
    ]
    
    # Convert to DataFrame
    parts_req_df = pd.DataFrame(parts_requirements)
    
    # Display with actions
    parts_req_df["action"] = ["Order", "Reserve", "Reserve"]
    
    st.dataframe(
        parts_req_df,
        column_config={
            "part_number": "Part Number",
            "description": "Description",
            "quantity": "Quantity",
            "status": "Status",
            "action": st.column_config.Column(
                "Action",
                width="small"
            )
        },
        use_container_width=True,
        hide_index=True
    )
    
    # Action buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Reserve All"):
            st.success("All available parts reserved for flight FL-1234")
    
    with col2:
        if st.button("Rush Order", type="primary"):
            st.success("Rush order created for missing parts")
    
    # Export options
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Export as PDF"):
            st.info("PDF export functionality would be implemented here")
    
    with col2:
        if st.button("Print Report"):
            st.info("Print functionality would be implemented here")