# Compliance Component
from shared_imports import *
@st.cache_resource
def init_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="your_mysql_password",  # Replace with your MySQL password
        database="aircraft_maintenance_db"
    )

def pre_flight_analysis():
    st.title("Pre-Flight Analysis")
    # Rest of your code
def compliance():
    st.title("Compliance Management")
    
    tab1, tab2, tab3 = st.tabs(["Certification Status", "Documentation", "Audit Preparation"])
    
    with tab1:
        st.subheader("Parts Certification Status")
        
        # Filtering options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_term = st.text_input("Search parts...", key="compliance_search")
        
        with col2:
            certification_statuses = ["All", "Certified", "Pending", "Expired", "Not Required"]
            status_filter = st.selectbox("Certification Status", options=certification_statuses)
        
        with col3:
            categories = ["All"] + [cat['category'] for cat in run_query("SELECT DISTINCT category FROM PARTS")]
            category = st.selectbox("Category", options=categories, key="compliance_category")
        
        # Build query based on filters
        query = """
            SELECT p.part_id, p.part_number, p.description, p.category, 
                   p.certification_status, p.certification_expiry, 
                   u.full_name as inspector_name,
                   p.document_reference
            FROM PARTS p
            LEFT JOIN USERS u ON p.inspector_id = u.user_id
            WHERE 1=1
        """
        
        params = []
        
        if search_term:
            query += " AND (p.part_number LIKE %s OR p.description LIKE %s)"
            search_param = f"%{search_term}%"
            params.extend([search_param, search_param])
        
        if status_filter and status_filter != "All":
            query += " AND p.certification_status = %s"
            params.append(status_filter)
        
        if category and category != "All":
            query += " AND p.category = %s"
            params.append(category)
        
        query += " ORDER BY p.part_number"
        
        # Execute query
        certification_data = run_query(query, params)
        
        # Convert to DataFrame for display
        if certification_data:
            cert_df = pd.DataFrame(certification_data)
            
            # Format date columns
            if 'certification_expiry' in cert_df.columns:
                cert_df['certification_expiry'] = cert_df['certification_expiry'].apply(
                    lambda x: x.strftime("%Y-%m-%d") if x else "N/A"
                )
            
            # Display the data
            st.dataframe(
                cert_df,
                column_config={
                    "part_id": None,  # Hide column
                    "part_number": "Part Number",
                    "description": "Description",
                    "category": "Category",
                    "certification_status": "Certification Status",
                    "certification_expiry": "Expiry Date",
                    "inspector_name": "Inspector",
                    "document_reference": "Document Reference"
                },
                use_container_width=True,
                hide_index=True,
                selection="single"
            )
            
            # Handle row selection for more details/actions
            if st.session_state.get('selected_rows'):
                selected_row = cert_df.iloc[st.session_state.selected_rows[0]]
                part_id = selected_row['part_id']
                
                with st.expander("Certification Details", expanded=True):
                    st.subheader(f"{selected_row['part_number']}: {selected_row['description']}")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Status:** {selected_row['certification_status']}")
                        st.write(f"**Expiry Date:** {selected_row['certification_expiry']}")
                        st.write(f"**Inspector:** {selected_row['inspector_name'] or 'N/A'}")
                        st.write(f"**Document Reference:** {selected_row['document_reference'] or 'N/A'}")
                    
                    with col2:
                        st.subheader("Actions")
                        
                        if st.button("Update Certification"):
                            st.session_state.update_certification_modal = True
                        
                        if st.button("View Document"):
                            st.info("Document viewer would be implemented here")
                        
                        if st.button("Print Certificate"):
                            st.info("Certificate printing would be implemented here")
            
            # Update Certification Modal
            if st.session_state.get('update_certification_modal', False):
                with st.form("update_certification_form"):
                    st.subheader("Update Certification")
                    
                    status_options = ["Certified", "Pending", "Expired", "Not Required"]
                    cert_status = st.selectbox("Certification Status", options=status_options)
                    cert_expiry = st.date_input("Expiry Date (if applicable)")
                    document_ref = st.text_input("Document Reference")
                    notes = st.text_area("Notes")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.form_submit_button("Save Changes"):
                            # Update certification in database
                            update_query = """
                                UPDATE PARTS
                                SET certification_status = %s,
                                    certification_expiry = %s,
                                    document_reference = %s,
                                    inspector_id = %s
                                WHERE part_id = %s
                            """
                            
                            params = (
                                cert_status,
                                cert_expiry,
                                document_ref,
                                st.session_state.user['user_id'],
                                part_id
                            )
                            
                            result = run_mutation(update_query, params)
                            
                            if result is not None:
                                st.success("Certification updated successfully!")
                                st.session_state.update_certification_modal = False
                                time.sleep(1)
                                st.experimental_rerun()
                            else:
                                st.error("Failed to update certification")
                    
                    with col2:
                        if st.form_submit_button("Cancel"):
                            st.session_state.update_certification_modal = False
                            st.experimental_rerun()
        else:
            st.info("No parts found matching your criteria")
    
    with tab2:
        st.subheader("Documentation Management")
        
        # Document categories
        doc_categories = ["Maintenance Manuals", "Certifications", "Inspection Records", 
                        "Regulatory Documents", "Supplier Documents", "Training Materials"]
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            selected_category = st.radio("Document Category", options=doc_categories)
            
            if st.button("Upload New Document"):
                st.session_state.upload_document_modal = True
        
        with col2:
            # Mock document data
            documents = [
                {"doc_id": 1, "title": "Boeing 737 Maintenance Manual", "category": "Maintenance Manuals", 
                "uploaded_by": "John Smith", "upload_date": "2025-01-15", "version": "2.4"},
                {"doc_id": 2, "title": "Airbus A320 Hydraulic System", "category": "Maintenance Manuals", 
                "uploaded_by": "Jane Doe", "upload_date": "2025-02-10", "version": "1.2"},
                {"doc_id": 3, "title": "Fuel Filter Certification", "category": "Certifications", 
                "uploaded_by": "Mike Johnson", "upload_date": "2025-03-05", "version": "1.0"},
                {"doc_id": 4, "title": "Quarterly Inspection Guide", "category": "Inspection Records", 
                "uploaded_by": "Sarah Wilson", "upload_date": "2025-02-22", "version": "3.1"},
                {"doc_id": 5, "title": "FAA Compliance Checklist", "category": "Regulatory Documents", 
                "uploaded_by": "John Smith", "upload_date": "2025-01-30", "version": "2023-Q1"},
                {"doc_id": 6, "title": "AeroParts Inc. Supplier Agreement", "category": "Supplier Documents", 
                "uploaded_by": "Jane Doe", "upload_date": "2025-03-15", "version": "1.3"},
                {"doc_id": 7, "title": "Maintenance Technician Training", "category": "Training Materials", 
                "uploaded_by": "Mike Johnson", "upload_date": "2025-02-05", "version": "2023-V2"}
            ]
            
            # Filter documents by selected category
            filtered_docs = [d for d in documents if d["category"] == selected_category]
            
            if filtered_docs:
                docs_df = pd.DataFrame(filtered_docs)
                
                st.dataframe(
                    docs_df,
                    column_config={
                        "doc_id": None,  # Hide column
                        "title": "Document Title",
                        "category": None,  # Hide column
                        "uploaded_by": "Uploaded By",
                        "upload_date": "Date",
                        "version": "Version"
                    },
                    use_container_width=True,
                    hide_index=True,
                    selection="single"
                )
                
                # Handle row selection
                if st.session_state.get('selected_rows'):
                    selected_doc = docs_df.iloc[st.session_state.selected_rows[0]]
                    
                    st.subheader(selected_doc["title"])
                    st.write(f"**Version:** {selected_doc['version']}")
                    st.write(f"**Uploaded By:** {selected_doc['uploaded_by']}")
                    st.write(f"**Date:** {selected_doc['upload_date']}")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("View Document"):
                            st.info("Document viewer would be implemented here")
                    
                    with col2:
                        if st.button("Download"):
                            st.info("Download functionality would be implemented here")
                    
                    with col3:
                        if st.button("Update Version"):
                            st.session_state.update_document_modal = True
            else:
                st.info(f"No documents found in category: {selected_category}")
                
                if st.button("Add First Document"):
                    st.session_state.upload_document_modal = True
        
        # Upload Document Modal
        if st.session_state.get('upload_document_modal', False):
            with st.form("upload_document_form"):
                st.subheader("Upload New Document")
                
                doc_title = st.text_input("Document Title *")
                doc_category = st.selectbox("Category *", options=doc_categories)
                doc_version = st.text_input("Version *")
                doc_file = st.file_uploader("Select File *", type=["pdf", "docx", "xlsx", "txt"])
                doc_description = st.text_area("Description")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.form_submit_button("Upload"):
                        if not doc_title or not doc_version or not doc_file:
                            st.error("Please fill in all required fields")
                        else:
                            # In a real app, this would save the file and add to database
                            st.success("Document uploaded successfully!")
                            st.session_state.upload_document_modal = False
                            time.sleep(1)
                            st.experimental_rerun()
                
                with col2:
                    if st.form_submit_button("Cancel"):
                        st.session_state.upload_document_modal = False
                        st.experimental_rerun()
        
        # Update Document Modal
        if st.session_state.get('update_document_modal', False):
            with st.form("update_document_form"):
                st.subheader("Update Document Version")
                
                new_version = st.text_input("New Version *")
                doc_file = st.file_uploader("Select Updated File *", type=["pdf", "docx", "xlsx", "txt"])
                change_notes = st.text_area("Change Notes")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.form_submit_button("Update"):
                        if not new_version or not doc_file:
                            st.error("Please fill in all required fields")
                        else:
                            # In a real app, this would save the file and update database
                            st.success("Document updated successfully!")
                            st.session_state.update_document_modal = False
                            time.sleep(1)
                            st.experimental_rerun()
                
                with col2:
                    if st.form_submit_button("Cancel"):
                        st.session_state.update_document_modal = False
                        st.experimental_rerun()
    
    with tab3:
        st.subheader("Audit Preparation")
        
        # Audit checklist
        col1, col2 = st.columns([1, 2])
        
        with col1:
            audit_types = ["FAA Compliance Audit", "Internal Quality Audit", "Supplier Audit"]
            selected_audit = st.selectbox("Audit Type", options=audit_types)
            
            audit_date = st.date_input("Scheduled Date")
            
            if st.button("Generate Audit Package"):
                with st.spinner("Generating audit package..."):
                    time.sleep(2)  # Simulate processing
                    st.success("Audit package generated successfully!")
        
        with col2:
            # Audit checklist based on selected type
            if selected_audit == "FAA Compliance Audit":
                checklist_items = [
                    "Parts inventory records",
                    "Maintenance documentation",
                    "Technician certifications",
                    "Repair station certification",
                    "Tool calibration records",
                    "Training records",
                    "Supplier qualifications",
                    "Quality manual compliance",
                    "Parts life tracking system",
                    "Non-conformance records"
                ]
            elif selected_audit == "Internal Quality Audit":
                checklist_items = [
                    "Inventory accuracy",
                    "Parts storage conditions",
                    "Shelf life monitoring",
                    "Return process",
                    "Tooling management",
                    "Work order documentation",
                    "Employee training status",
                    "Safety procedures",
                    "Internal process compliance",
                    "Continuous improvement initiatives"
                ]
            else:  # Supplier Audit
                checklist_items = [
                    "Parts quality inspection",
                    "Delivery performance",
                    "Certificate of conformance",
                    "Manufacturing process controls",
                    "Corrective action processes",
                    "Quality management system",
                    "Employee qualifications",
                    "Material traceability",
                    "Facility conditions",
                    "Handling of non-conforming products"
                ]
            
            # Display checklist with checkboxes
            st.subheader("Audit Checklist")
            
            for item in checklist_items:
                st.checkbox(item, key=f"audit_{item}")
            
            if st.button("Save Checklist Progress"):
                st.success("Checklist progress saved!")
        
        # Compliance metrics
        st.subheader("Current Compliance Metrics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Documentation Compliance", "94%", delta="2%")
        
        with col2:
            st.metric("Parts Certification", "89%", delta="-3%")
        
        with col3:
            st.metric("Training Compliance", "97%", delta="5%")
        
        # Compliance issues
        st.subheader("Open Compliance Issues")
        
        issues = [
            {"id": 1, "description": "Missing certification for 5 hydraulic components", "severity": "High", "due_date": "2025-04-15", "assigned_to": "John Smith"},
            {"id": 2, "description": "Outdated maintenance manual for Airbus A320", "severity": "Medium", "due_date": "2025-04-20", "assigned_to": "Jane Doe"},
            {"id": 3, "description": "Calibration overdue for 3 torque wrenches", "severity": "Medium", "due_date": "2025-04-10", "assigned_to": "Mike Johnson"},
            {"id": 4, "description": "Supplier qualification expired for AeroParts Inc.", "severity": "High", "due_date": "2025-04-05", "assigned_to": "Sarah Wilson"}
        ]
        
        issues_df = pd.DataFrame(issues)
        
        st.dataframe(
            issues_df,
            column_config={
                "id": None,
                "description": "Issue Description",
                "severity": st.column_config.Column(
                    "Severity",
                    width="small"
                ),
                "due_date": "Due Date",
                "assigned_to": "Assigned To"
            },
            use_container_width=True,
            hide_index=True
        )
        
        if st.button("Add New Issue"):
            st.session_state.add_issue_modal = True
        
        # Add Issue Modal
        if st.session_state.get('add_issue_modal', False):
            with st.form("add_issue_form"):
                st.subheader("Add Compliance Issue")
                
                issue_desc = st.text_area("Issue Description *")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    severity = st.selectbox("Severity *", options=["Low", "Medium", "High"])
                
                with col2:
                    due_date = st.date_input("Due Date *")
                
                assignee = st.selectbox("Assign To *", options=["John Smith", "Jane Doe", "Mike Johnson", "Sarah Wilson"])
                
                notes = st.text_area("Additional Notes")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.form_submit_button("Add Issue"):
                        if not issue_desc:
                            st.error("Please fill in all required fields")
                        else:
                            # In a real app, this would add to database
                            st.success("Compliance issue added successfully!")
                            st.session_state.add_issue_modal = False
                            time.sleep(1)
                            st.experimental_rerun()
                
                with col2:
                    if st.form_submit_button("Cancel"):
                        st.session_state.add_issue_modal = False
                        st.experimental_rerun()