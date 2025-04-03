# Transfers Component
from shared_imports import *

def pre_flight_analysis():
    st.title("Pre-Flight Analysis")
    # Rest of your code
def transfers():
    st.title("Part Transfers")
    
    tab1, tab2 = st.tabs(["View Transfers", "Create Transfer"])
    
    with tab1:
        # Filtering options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_term = st.text_input("Search transfers...", key="transfer_search")
        
        with col2:
            statuses = ["All", "Pending", "In Transit", "Completed", "Cancelled"]
            status_filter = st.selectbox("Status", options=statuses)
        
        with col3:
            # For simplicity in prototype, hardcode date ranges
            date_ranges = ["All Time", "Today", "Last 7 Days", "Last 30 Days"]
            date_range = st.selectbox("Date Range", options=date_ranges)
        
        # Build query based on filters
        query = """
            SELECT it.transaction_id, it.transaction_time, 
                   p.part_number, p.description, it.quantity,
                   sf.facility_name as source_facility,
                   df.facility_name as destination_facility,
                   u.full_name as initiated_by,
                   it.status, it.completion_time, it.reference_number
            FROM INVENTORY_TRANSACTIONS it
            JOIN PARTS p ON it.part_id = p.part_id
            JOIN USERS u ON it.user_id = u.user_id
            LEFT JOIN FACILITIES sf ON it.source_facility_id = sf.facility_id
            LEFT JOIN FACILITIES df ON it.destination_facility_id = df.facility_id
            WHERE it.transaction_type = 'TRANSFER'
        """
        
        params = []
        
        if search_term:
            query += """ AND (p.part_number LIKE %s OR p.description LIKE %s 
                           OR sf.facility_name LIKE %s OR df.facility_name LIKE %s)"""
            search_param = f"%{search_term}%"
            params.extend([search_param, search_param, search_param, search_param])
        
        if status_filter and status_filter != "All":
            query += " AND it.status = %s"
            params.append(status_filter)
        
        if date_range == "Today":
            query += " AND DATE(it.transaction_time) = CURDATE()"
        elif date_range == "Last 7 Days":
            query += " AND it.transaction_time >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
        elif date_range == "Last 30 Days":
            query += " AND it.transaction_time >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)"
        
        query += " ORDER BY it.transaction_time DESC"
        
        # Execute query
        transfer_data = run_query(query, params)
        
        # Convert to DataFrame for display
        if transfer_data and len(transfer_data) > 0:
            df = pd.DataFrame(transfer_data)
            
            # Format datetime columns
            if 'transaction_time' in df.columns:
                df['transaction_time'] = df['transaction_time'].apply(lambda x: x.strftime("%Y-%m-%d %H:%M") if x else "")
            
            if 'completion_time' in df.columns:
                df['completion_time'] = df['completion_time'].apply(lambda x: x.strftime("%Y-%m-%d %H:%M") if x else "")
            
            # Display the data
            st.dataframe(
                df,
                column_config={
                    "transaction_id": None,  # Hide column
                    "part_number": "Part #",
                    "description": "Description",
                    "quantity": "Qty",
                    "source_facility": "From",
                    "destination_facility": "To",
                    "initiated_by": "Initiated By",
                    "status": "Status",
                    "transaction_time": "Transfer Time",
                    "completion_time": "Completion Time",
                    "reference_number": "Reference #"
                },
                use_container_width=True,
                hide_index=True,
                selection="single"
            )
            
            # Handle row selection for more details/actions
            if st.session_state.get('selected_rows'):
                selected_row = df.iloc[st.session_state.selected_rows[0]]
                transaction_id = selected_row['transaction_id']
                
                with st.expander("Transfer Details", expanded=True):
                    st.subheader(f"Transfer #{transaction_id}")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Part:** {selected_row['part_number']} - {selected_row['description']}")
                        st.write(f"**Quantity:** {selected_row['quantity']}")
                        st.write(f"**From:** {selected_row['source_facility']}")
                        st.write(f"**To:** {selected_row['destination_facility']}")
                    
                    with col2:
                        st.write(f"**Status:** {selected_row['status']}")
                        st.write(f"**Initiated By:** {selected_row['initiated_by']}")
                        st.write(f"**Transfer Time:** {selected_row['transaction_time']}")
                        st.write(f"**Completion Time:** {selected_row['completion_time'] or 'N/A'}")
                        st.write(f"**Reference #:** {selected_row['reference_number'] or 'N/A'}")
                    
                    # Action buttons based on status
                    st.subheader("Actions")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if selected_row['status'] == 'Pending':
                            if st.button("Mark as In Transit"):
                                run_mutation("""
                                    UPDATE INVENTORY_TRANSACTIONS 
                                    SET status = 'In Transit'
                                    WHERE transaction_id = %s
                                """, (transaction_id,))
                                st.success("Transfer marked as In Transit")
                                time.sleep(1)
                                st.experimental_rerun()
                        elif selected_row['status'] == 'In Transit':
                            if st.button("Mark as Completed"):
                                run_mutation("""
                                    UPDATE INVENTORY_TRANSACTIONS 
                                    SET status = 'Completed', completion_time = NOW()
                                    WHERE transaction_id = %s
                                """, (transaction_id,))
                                st.success("Transfer completed")
                                time.sleep(1)
                                st.experimental_rerun()
                    
                    with col2:
                        if selected_row['status'] in ['Pending', 'In Transit']:
                            if st.button("Cancel Transfer"):
                                run_mutation("""
                                    UPDATE INVENTORY_TRANSACTIONS 
                                    SET status = 'Cancelled'
                                    WHERE transaction_id = %s
                                """, (transaction_id,))
                                st.success("Transfer cancelled")
                                time.sleep(1)
                                st.experimental_rerun()
        else:
            st.info("No transfers found matching your criteria")
    
    with tab2:
        # Create new transfer form
        st.subheader("Create New Transfer")
        
        # Get all parts with stock
        parts_query = """
            SELECT p.part_id, p.part_number, p.description,
                   (SELECT COALESCE(SUM(CASE WHEN transaction_type = 'IN' THEN quantity ELSE -quantity END), 0)
                    FROM INVENTORY_TRANSACTIONS
                    WHERE part_id = p.part_id
                    AND status = 'AVAILABLE') as stock
            FROM PARTS p
            HAVING stock > 0
            ORDER BY p.part_number
        """
        
        parts = run_query(parts_query)
        
        if not parts or len(parts) == 0:
            st.warning("No parts available for transfer")
        else:
            # Get all facilities
            facilities = run_query("SELECT facility_id, facility_name FROM FACILITIES WHERE is_active = 1")
            
            col1, col2 = st.columns(2)
            
            with col1:
                part_options = [f"{p['part_number']} - {p['description']} (Stock: {p['stock']})" for p in parts]
                selected_part = st.selectbox("Select Part *", options=part_options)
                
                # Get selected part ID and stock
                selected_part_id = None
                max_stock = 0
                if selected_part:
                    part_number = selected_part.split(" - ")[0]
                    for p in parts:
                        if p['part_number'] == part_number:
                            selected_part_id = p['part_id']
                            max_stock = p['stock']
                            break
                
                # Get source facility (current user's facility)
                user_facility = run_query("""
                    SELECT f.* FROM USERS u
                    JOIN FACILITIES f ON u.facility_id = f.facility_id
                    WHERE u.user_id = %s
                """, (st.session_state.user['user_id'],))
                
                source_facility = user_facility[0] if user_facility else None
                source_name = source_facility['facility_name'] if source_facility else "Unknown"
                st.text_input("From Facility", value=source_name, disabled=True)
            
            with col2:
                # Destination facility cannot be the same as source
                dest_facilities = [f for f in facilities if not source_facility or f['facility_id'] != source_facility['facility_id']]
                dest_options = [f['facility_name'] for f in dest_facilities]
                selected_dest = st.selectbox("To Facility *", options=dest_options)
                
                # Get selected destination ID
                dest_facility_id = None
                for f in dest_facilities:
                    if f['facility_name'] == selected_dest:
                        dest_facility_id = f['facility_id']
                        break
                
                # Quantity
                quantity = st.number_input("Quantity *", min_value=1, max_value=max_stock, step=1)
            
            # Reference number
            reference = st.text_input("Reference Number (Optional)", placeholder="e.g., Work Order Number")
            
            # Notes
            notes = st.text_area("Notes", placeholder="Optional additional information")
            
            # Submit button
            if st.button("Submit Transfer"):
                if not selected_part_id or not dest_facility_id or quantity <= 0:
                    st.error("Please fill in all required fields")
                elif quantity > max_stock:
                    st.error(f"Quantity exceeds available stock ({max_stock})")
                else:
                    # Insert the new transfer
                    insert_query = """
                        INSERT INTO INVENTORY_TRANSACTIONS 
                        (part_id, transaction_type, quantity, source_facility_id, destination_facility_id,
                         status, transaction_time, user_id, reference_number, notes)
                        VALUES (%s, 'TRANSFER', %s, %s, %s, 'Pending', NOW(), %s, %s, %s)
                    """
                    
                    params = (
                        selected_part_id, quantity, source_facility['facility_id'], 
                        dest_facility_id, st.session_state.user['user_id'],
                        reference, notes
                    )
                    
                    result = run_mutation(insert_query, params)
                    
                    if result:
                        st.success("Transfer created successfully!")
                        # Clear form fields
                        st.experimental_rerun()
                    else:
                        st.error("Failed to create transfer. Please try again.")