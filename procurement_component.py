# Procurement Component
from shared_imports import *
from db import run_query, run_mutation

def procurement():
    st.title("Procurement")
    
    tab1, tab2 = st.tabs(["Purchase Orders", "Create Order"])
    
    with tab1:
        # Filtering options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_term = st.text_input("Search orders...", key="order_search")
        
        with col2:
            statuses = ["All", "Pending", "Approved", "Ordered", "Delivered", "Cancelled"]
            status_filter = st.selectbox("Status", options=statuses)
        
        with col3:
            # For simplicity in prototype, hardcode date ranges
            date_ranges = ["All Time", "Today", "Last 7 Days", "Last 30 Days"]
            date_range = st.selectbox("Date Range", options=date_ranges)
        
        # In a real application, this would query a purchase_orders table
        # For prototype, use mock data
        orders = [
            {
                "order_id": "PO-12345",
                "parts": "Fuel Filters, Hydraulic Sensors",
                "quantity": 10,
                "total_cost": 1250.00,
                "supplier": "AeroParts Inc.",
                "status": "Delivered",
                "order_date": "2025-03-25",
                "delivery_date": "2025-03-30"
            },
            {
                "order_id": "PO-12346",
                "parts": "Oil Separators",
                "quantity": 5,
                "total_cost": 875.50,
                "supplier": "Global Aviation Supply",
                "status": "Ordered",
                "order_date": "2025-03-28",
                "delivery_date": "2025-04-05"
            },
            {
                "order_id": "PO-12347",
                "parts": "Control Switches, Circuit Boards",
                "quantity": 15,
                "total_cost": 3200.75,
                "supplier": "Precision Aircraft Components",
                "status": "Pending",
                "order_date": "2025-04-01",
                "delivery_date": None
            }
        ]
        
        # Filter based on search term
        if search_term:
            orders = [o for o in orders if search_term.lower() in o["order_id"].lower() or 
                      search_term.lower() in o["parts"].lower() or 
                      search_term.lower() in o["supplier"].lower()]
        
        # Filter based on status
        if status_filter and status_filter != "All":
            orders = [o for o in orders if o["status"] == status_filter]
        
        # Convert to DataFrame for display
        if orders:
            orders_df = pd.DataFrame(orders)
            
            # Display the data
            st.dataframe(
                orders_df,
                column_config={
                    "order_id": "Order #",
                    "parts": "Parts",
                    "quantity": "Qty",
                    "total_cost": st.column_config.NumberColumn(
                        "Total Cost",
                        format="$%.2f"
                    ),
                    "supplier": "Supplier",
                    "status": "Status",
                    "order_date": "Order Date",
                    "delivery_date": "Delivery Date"
                },
                use_container_width=True,
                hide_index=True,
            )
            
            # Handle row selection for more details/actions
            if st.session_state.get('selected_rows'):
                selected_row = orders_df.iloc[st.session_state.selected_rows[0]]
                order_id = selected_row['order_id']
                
                with st.expander("Order Details", expanded=True):
                    st.subheader(f"Purchase Order: {order_id}")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Parts:** {selected_row['parts']}")
                        st.write(f"**Quantity:** {selected_row['quantity']}")
                        st.write(f"**Total Cost:** ${selected_row['total_cost']:.2f}")
                        st.write(f"**Supplier:** {selected_row['supplier']}")
                    
                    with col2:
                        st.write(f"**Status:** {selected_row['status']}")
                        st.write(f"**Order Date:** {selected_row['order_date']}")
                        st.write(f"**Expected Delivery:** {selected_row['delivery_date'] or 'N/A'}")
                    
                    # Order details (mock data)
                    st.subheader("Order Line Items")
                    
                    line_items = [
                        {"part_number": "P-12345", "description": "Fuel Filter", "quantity": 5, "unit_price": 125.00, "total": 625.00},
                        {"part_number": "P-24680", "description": "Hydraulic Sensor", "quantity": 5, "unit_price": 125.00, "total": 625.00}
                    ]
                    
                    line_items_df = pd.DataFrame(line_items)
                    st.dataframe(line_items_df, use_container_width=True, hide_index=True)
                    
                    # Action buttons based on status
                    st.subheader("Actions")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if selected_row['status'] == 'Pending':
                            if st.button("Approve Order"):
                                st.success("Order approved and sent to supplier")
                        elif selected_row['status'] == 'Ordered':
                            if st.button("Mark as Delivered"):
                                st.success("Order marked as delivered")
                    
                    with col2:
                        if selected_row['status'] in ['Pending', 'Approved']:
                            if st.button("Cancel Order"):
                                st.success("Order cancelled")
                    
                    with col3:
                        if st.button("Print Order"):
                            st.info("Print functionality would be implemented here")
        else:
            st.info("No purchase orders found matching your criteria")
    
    with tab2:
        # Create new order form
        st.subheader("Create Purchase Order")
        
        # Get all suppliers (mock data for prototype)
        suppliers = [
            {"supplier_id": 1, "name": "AeroParts Inc.", "reliability": 0.95},
            {"supplier_id": 2, "name": "Global Aviation Supply", "reliability": 0.88},
            {"supplier_id": 3, "name": "Precision Aircraft Components", "reliability": 0.92}
        ]
        
        # Get parts with low stock
        low_stock_query = """
            SELECT p.part_id, p.part_number, p.description, p.category, p.unit_cost,
                   (SELECT COALESCE(SUM(CASE WHEN transaction_type = 'IN' THEN quantity ELSE -quantity END), 0)
                    FROM INVENTORY_TRANSACTIONS
                    WHERE part_id = p.part_id) as in_stock,
                   p.minimum_stock
            FROM PARTS p
            HAVING in_stock < p.minimum_stock OR in_stock IS NULL
            ORDER BY (in_stock - p.minimum_stock)
        """
        
        low_stock_parts = run_query(low_stock_query)
        
        # Convert to DataFrame for display
        if low_stock_parts:
            low_stock_df = pd.DataFrame(low_stock_parts)
            
            # Add columns for ordering
            low_stock_df['to_order'] = low_stock_df['minimum_stock'] - low_stock_df['in_stock']
            low_stock_df['to_order'] = low_stock_df['to_order'].apply(lambda x: max(x, 0))
            low_stock_df['select'] = False
            
            # Display the parts that need to be ordered
            st.subheader("Parts Below Minimum Stock")
            
            # Allow user to select parts to order
            edited_df = st.data_editor(
                low_stock_df,
                column_config={
                    "part_id": None,  # Hide column
                    "part_number": "Part Number",
                    "description": "Description",
                    "category": "Category",
                    "in_stock": "In Stock",
                    "minimum_stock": "Min Stock",
                    "to_order": st.column_config.NumberColumn(
                        "Quantity to Order",
                        min_value=0,
                        step=1
                    ),
                    "unit_cost": st.column_config.NumberColumn(
                        "Unit Cost",
                        format="$%.2f"
                    ),
                    "select": "Select"
                },
                use_container_width=True,
                hide_index=True,
                disabled=["part_id", "part_number", "description", "category", "in_stock", "minimum_stock", "unit_cost"]
            )
            
            # Create order form
            col1, col2 = st.columns(2)
            
            with col1:
                supplier_options = [s["name"] for s in suppliers]
                selected_supplier = st.selectbox("Supplier", options=supplier_options)
            
            with col2:
                priority = st.selectbox("Priority", options=["Normal", "Rush", "Emergency"])
            
            notes = st.text_area("Order Notes", placeholder="Special instructions or additional information")
            
            # Calculate total
            selected_parts = edited_df[edited_df['select'] == True]
            total_cost = sum(selected_parts['to_order'] * selected_parts['unit_cost'])
            
            st.write(f"**Total Cost:** ${total_cost:.2f}")
            
            # Submit button
            if st.button("Create Purchase Order"):
                if len(selected_parts) == 0:
                    st.error("Please select at least one part to order")
                else:
                    # In a real application, this would create an order in the database
                    st.success("Purchase order created successfully!")