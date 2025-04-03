# Reports Component
from shared_imports import *
from db import run_query, run_mutation


def reports():
    st.title("Reports")
    
    report_types = [
        "Inventory Summary",
        "Part Usage History",
        "Maintenance Requests Analysis",
        "Part Expiration Report",
        "Compliance Status",
        "Cost Analysis"
    ]
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        selected_report = st.radio("Select Report", options=report_types)
        
        # Date range selector
        st.subheader("Date Range")
        date_range = st.selectbox(
            "Predefined Range",
            options=["Last 7 Days", "Last 30 Days", "Last 90 Days", "Last Year", "Custom"]
        )
        
        if date_range == "Custom":
            start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
            end_date = st.date_input("End Date", value=datetime.now())
        else:
            if date_range == "Last 7 Days":
                delta = 7
            elif date_range == "Last 30 Days":
                delta = 30
            elif date_range == "Last 90 Days":
                delta = 90
            else:  # Last Year
                delta = 365
            
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=delta)
        
        # Export options
        st.subheader("Export")
        export_format = st.selectbox(
            "Format",
            options=["Excel", "CSV", "PDF"]
        )
        
        if st.button("Export Report"):
            st.success(f"Report would be exported as {export_format}")
    
    with col2:
        if selected_report == "Inventory Summary":
            inventory_summary_report(start_date, end_date)
        elif selected_report == "Part Usage History":
            part_usage_history_report(start_date, end_date)
        elif selected_report == "Maintenance Requests Analysis":
            maintenance_requests_report(start_date, end_date)
        elif selected_report == "Part Expiration Report":
            part_expiration_report()
        elif selected_report == "Compliance Status":
            compliance_status_report()
        elif selected_report == "Cost Analysis":
            cost_analysis_report(start_date, end_date)

# Individual Report Functions
def inventory_summary_report(start_date, end_date):
    st.subheader("Inventory Summary Report")
    
    # Get category breakdown
    categories_query = """
        SELECT p.category, COUNT(*) as part_count,
               SUM(p.unit_cost * 
                  (SELECT COALESCE(SUM(CASE WHEN transaction_type = 'IN' THEN quantity ELSE -quantity END), 0)
                   FROM INVENTORY_TRANSACTIONS
                   WHERE part_id = p.part_id)) as total_value
        FROM PARTS p
        GROUP BY p.category
        ORDER BY total_value DESC
    """
    
    categories_data = run_query(categories_query)
    
    if categories_data:
        # Create pie chart for part count by category
        fig1 = px.pie(
            categories_data,
            values='part_count',
            names='category',
            title='Parts Count by Category'
        )
        st.plotly_chart(fig1, use_container_width=True)
        
        # Create bar chart for total value by category
        fig2 = px.bar(
            categories_data,
            x='category',
            y='total_value',
            title='Inventory Value by Category',
            labels={'total_value': 'Total Value ($)', 'category': 'Category'}
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # Inventory levels over time (mock data for prototype)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    inventory_data = {
        'date': dates,
        'count': [1000 + i * 10 + np.random.randint(-20, 20) for i in range(len(dates))]
    }
    inventory_df = pd.DataFrame(inventory_data)
    
    # Create line chart for inventory levels
    fig3 = px.line(
        inventory_df,
        x='date',
        y='count',
        title='Inventory Levels Over Time',
        labels={'count': 'Parts Count', 'date': 'Date'}
    )
    st.plotly_chart(fig3, use_container_width=True)
    
    # Facilities breakdown
    facilities_query = """
        SELECT f.facility_name,
               COUNT(DISTINCT it.part_id) as unique_parts,
               SUM(it.quantity) as total_parts
        FROM FACILITIES f
        JOIN INVENTORY_TRANSACTIONS it ON f.facility_id = it.destination_facility_id
        WHERE it.status = 'AVAILABLE'
        GROUP BY f.facility_name
        ORDER BY total_parts DESC
    """
    
    facilities_data = run_query(facilities_query)
    
    if facilities_data:
        st.subheader("Inventory by Facility")
        facilities_df = pd.DataFrame(facilities_data)
        st.dataframe(facilities_df, use_container_width=True)

def part_usage_history_report(start_date, end_date):
    st.subheader("Part Usage History Report")
    
    # Get top used parts
    usage_query = """
        SELECT p.part_number, p.description, p.category,
               SUM(it.quantity) as quantity_used
        FROM INVENTORY_TRANSACTIONS it
        JOIN PARTS p ON it.part_id = p.part_id
        WHERE it.transaction_type = 'OUT'
        AND it.transaction_time BETWEEN %s AND %s
        GROUP BY p.part_id
        ORDER BY quantity_used DESC
        LIMIT 10
    """
    
    usage_data = run_query(usage_query, (start_date, end_date))
    
    if usage_data:
        usage_df = pd.DataFrame(usage_data)
        
        # Create horizontal bar chart
        fig = px.bar(
            usage_df,
            y='part_number',
            x='quantity_used',
            title='Top 10 Most Used Parts',
            labels={'quantity_used': 'Quantity Used', 'part_number': 'Part Number'},
            orientation='h',
            hover_data=['description', 'category']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Usage trend over time (mock data for prototype)
    # In a real application, this would query the database
    dates = pd.date_range(start=start_date, end=end_date, freq='W')
    parts = ['P-12345', 'P-67890', 'P-24680', 'P-13579', 'P-97531']
    
    usage_trend_data = []
    for part in parts:
        for date in dates:
            usage_trend_data.append({
                'date': date,
                'part_number': part,
                'quantity': np.random.randint(1, 10)
            })
    
    usage_trend_df = pd.DataFrame(usage_trend_data)
    
    # Create line chart for usage trend
    fig2 = px.line(
        usage_trend_df,
        x='date',
        y='quantity',
        color='part_number',
        title='Part Usage Trends',
        labels={'quantity': 'Quantity Used', 'date': 'Date', 'part_number': 'Part Number'}
    )
    st.plotly_chart(fig2, use_container_width=True)
    
    # Recent usage table
    recent_usage_query = """
        SELECT p.part_number, p.description, it.quantity,
               u.full_name as used_by, f.facility_name,
               it.transaction_time
        FROM INVENTORY_TRANSACTIONS it
        JOIN PARTS p ON it.part_id = p.part_id
        JOIN USERS u ON it.user_id = u.user_id
        JOIN FACILITIES f ON it.source_facility_id = f.facility_id
        WHERE it.transaction_type = 'OUT'
        AND it.transaction_time BETWEEN %s AND %s
        ORDER BY it.transaction_time DESC
        LIMIT 20
    """
    
    recent_usage = run_query(recent_usage_query, (start_date, end_date))
    
    if recent_usage:
        st.subheader("Recent Usage Details")
        recent_df = pd.DataFrame(recent_usage)
        # Format datetime
        recent_df['transaction_time'] = recent_df['transaction_time'].apply(lambda x: x.strftime("%Y-%m-%d %H:%M") if x else "")
        st.dataframe(recent_df, use_container_width=True)

def maintenance_requests_report(start_date, end_date):
    st.subheader("Maintenance Requests Analysis")
    
    # Status breakdown
    status_query = """
        SELECT status, COUNT(*) as count
        FROM MAINTENANCE_REQUESTS
        WHERE request_time BETWEEN %s AND %s
        GROUP BY status
    """
    
    status_data = run_query(status_query, (start_date, end_date))
    
    if status_data:
        status_df = pd.DataFrame(status_data)
        
        # Create pie chart for status breakdown
        fig1 = px.pie(
            status_df,
            values='count',
            names='status',
            title='Maintenance Requests by Status'
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    # Requests by aircraft type
    aircraft_query = """
        SELECT aircraft_model, COUNT(*) as request_count
        FROM MAINTENANCE_REQUESTS
        WHERE request_time BETWEEN %s AND %s
        GROUP BY aircraft_model
        ORDER BY request_count DESC
    """
    
    aircraft_data = run_query(aircraft_query, (start_date, end_date))
    
    if aircraft_data:
        aircraft_df = pd.DataFrame(aircraft_data)
        
        # Create bar chart for requests by aircraft
        fig2 = px.bar(
            aircraft_df,
            x='aircraft_model',
            y='request_count',
            title='Maintenance Requests by Aircraft Model',
            labels={'request_count': 'Number of Requests', 'aircraft_model': 'Aircraft Model'}
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # Response time analysis (mock data for prototype)
    # In a real application, this would calculate from request_time and completion_time
    response_times = [{
        'priority': p,
        'avg_response_hours': np.random.randint(1, 24)
    } for p in ['High', 'Medium', 'Low']]
    
    response_df = pd.DataFrame(response_times)
    
    # Create bar chart for response times
    fig3 = px.bar(
        response_df,
        x='priority',
        y='avg_response_hours',
        title='Average Response Time by Priority',
        labels={'avg_response_hours': 'Average Hours', 'priority': 'Priority'}
    )
    st.plotly_chart(fig3, use_container_width=True)

def part_expiration_report():
    st.subheader("Part Expiration Report")
    
    # Get parts expiring soon
    expiration_query = """
        SELECT p.part_number, p.description, p.category,
               p.expiration_date,
               DATEDIFF(p.expiration_date, CURDATE()) as days_remaining,
               (SELECT COALESCE(SUM(CASE WHEN transaction_type = 'IN' THEN quantity ELSE -quantity END), 0)
                FROM INVENTORY_TRANSACTIONS
                WHERE part_id = p.part_id) as quantity
        FROM PARTS p
        WHERE p.expiration_date IS NOT NULL
        ORDER BY days_remaining
    """
    
    expiration_data = run_query(expiration_query)
    
    if expiration_data:
        exp_df = pd.DataFrame(expiration_data)
        
        # Add expiration warning
        def expiration_status(days):
            if days < 0:
                return "Expired"
            elif days <= 7:
                return "Critical"
            elif days <= 30:
                return "Warning"
            else:
                return "OK"
        
        exp_df['status'] = exp_df['days_remaining'].apply(expiration_status)
        
        # Create a color map for status
        color_map = {
            "Expired": "#ff0000",
            "Critical": "#ff6666",
            "Warning": "#ffcc00",
            "OK": "#00cc66"
        }
        
        # Create bar chart for expiration status
        fig = px.bar(
            exp_df,
            x='part_number',
            y='days_remaining',
            color='status',
            color_discrete_map=color_map,
            title='Days Until Part Expiration',
            labels={'days_remaining': 'Days Remaining', 'part_number': 'Part Number'},
            hover_data=['description', 'category', 'quantity', 'expiration_date']
        )
        
        # Add a horizontal line at 0 days
        fig.add_shape(
            type="line",
            x0=-0.5,
            y0=0,
            x1=len(exp_df) - 0.5,
            y1=0,
            line=dict(
                color="Red",
                width=2,
                dash="dash",
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Display table of expiring parts
        st.subheader("Expiring Parts Details")
        
        # Format expiration date
        exp_df['expiration_date'] = exp_df['expiration_date'].apply(lambda x: x.strftime("%Y-%m-%d") if x else "")
        
        # Display with color coding
        st.dataframe(
            exp_df,
            column_config={
                "part_number": "Part Number",
                "description": "Description",
                "category": "Category",
                "expiration_date": "Expiration Date",
                "days_remaining": "Days Remaining",
                "quantity": "Quantity in Stock",
                "status": st.column_config.Column(
                    "Status",
                    width="small"
                )
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No parts with expiration dates found")

def compliance_status_report():
    st.subheader("Compliance Status Report")
    
    # Get certification status
    certification_query = """
        SELECT certification_status, COUNT(*) as count
        FROM PARTS
        GROUP BY certification_status
    """
    
    certification_data = run_query(certification_query)
    
    if certification_data:
        cert_df = pd.DataFrame(certification_data)
        
        # Create pie chart for certification status
        fig1 = px.pie(
            cert_df,
            values='count',
            names='certification_status',
            title='Parts by Certification Status'
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    # Inspection status (mock data for prototype)
    inspection_data = [
        {"status": "Up to Date", "count": 850},
        {"status": "Due Soon", "count": 120},
        {"status": "Overdue", "count": 65}
    ]
    
    insp_df = pd.DataFrame(inspection_data)
    
    # Create pie chart for inspection status
    fig2 = px.pie(
        insp_df,
        values='count',
        names='status',
        title='Parts by Inspection Status',
        color='status',
        color_discrete_map={
            "Up to Date": "#00cc66",
            "Due Soon": "#ffcc00",
            "Overdue": "#ff0000"
        }
    )
    st.plotly_chart(fig2, use_container_width=True)
    
    # Parts with documentation issues (mock data for prototype)
    docs_issues = [
        {"part_number": "P-12345", "description": "Fuel Filter", "issue": "Missing certification", "severity": "High"},
        {"part_number": "P-67890", "description": "Oil Separator", "issue": "Outdated documentation", "severity": "Medium"},
        {"part_number": "P-24680", "description": "Hydraulic Sensor", "issue": "Incorrect part number in docs", "severity": "Low"},
        {"part_number": "P-13579", "description": "Air Filter", "issue": "Missing inspection record", "severity": "High"},
        {"part_number": "P-97531", "description": "Pressure Valve", "issue": "Unsigned certification", "severity": "Medium"}
    ]
    
    st.subheader("Documentation Issues")
    docs_df = pd.DataFrame(docs_issues)
    
    # Display documentation issues
    st.dataframe(
        docs_df,
        column_config={
            "part_number": "Part Number",
            "description": "Description",
            "issue": "Issue",
            "severity": st.column_config.Column(
                "Severity",
                width="small"
            )
        },
        use_container_width=True,
        hide_index=True
    )

def cost_analysis_report(start_date, end_date):
    st.subheader("Cost Analysis Report")
    
    # Total inventory value
    value_query = """
        SELECT 
            SUM(p.unit_cost * 
               (SELECT COALESCE(SUM(CASE WHEN transaction_type = 'IN' THEN quantity ELSE -quantity END), 0)
                FROM INVENTORY_TRANSACTIONS
                WHERE part_id = p.part_id)) as total_value
        FROM PARTS p
    """
    
    value_data = run_query(value_query)
    total_value = value_data[0]['total_value'] if value_data and value_data[0]['total_value'] else 0
    
    # Cost by category
    category_cost_query = """
        SELECT p.category,
               SUM(p.unit_cost * 
                  (SELECT COALESCE(SUM(CASE WHEN transaction_type = 'IN' THEN quantity ELSE -quantity END), 0)
                   FROM INVENTORY_TRANSACTIONS
                   WHERE part_id = p.part_id)) as category_value
        FROM PARTS p
        GROUP BY p.category
        ORDER BY category_value DESC
    """
    
    category_cost_data = run_query(category_cost_query)
    
    # Monthly spending (mock data for prototype)
    # In a real application, this would query transaction history with dates
    months = pd.date_range(start=start_date, end=end_date, freq='M')
    
    monthly_spending = []
    for month in months:
        monthly_spending.append({
            'month': month.strftime("%Y-%m"),
            'procurement': np.random.randint(10000, 50000),
            'emergency': np.random.randint(1000, 10000),
            'shipping': np.random.randint(500, 5000)
        })
    
    monthly_df = pd.DataFrame(monthly_spending)
    
    # Create summary metrics
    st.metric("Total Inventory Value", f"${total_value:,.2f}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Monthly Average Spend", "$25,360.00")
    
    with col2:
        st.metric("Emergency Purchase %", "18%", delta="-5%")
    
    # Display category cost breakdown
    if category_cost_data:
        cat_cost_df = pd.DataFrame(category_cost_data)
        
        # Create a horizontal bar chart for category costs
        fig1 = px.bar(
            cat_cost_df,
            y='category',
            x='category_value',
            title='Inventory Value by Category',
            labels={'category_value': 'Value ($)', 'category': 'Category'},
            orientation='h'
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    # Create a stacked bar chart for monthly spending
    fig2 = px.bar(
        monthly_df,
        x='month',
        y=['procurement', 'emergency', 'shipping'],
        title='Monthly Spending Breakdown',
        labels={'value': 'Amount ($)', 'month': 'Month', 'variable': 'Type'},
        color_discrete_map={
            'procurement': '#3366cc',
            'emergency': '#dc3545',
            'shipping': '#ffc107'
        }
    )
    st.plotly_chart(fig2, use_container_width=True)
    
    # Cost-saving opportunities (mock data for prototype)
    opportunities = [
        {"category": "Emergency Orders", "current_cost": 120000, "potential_savings": 90000, 
         "action": "Implement predictive maintenance to reduce emergency purchases"},
        {"category": "Inventory Holding", "current_cost": 80000, "potential_savings": 30000, 
         "action": "Optimize inventory levels to reduce excess stock"},
        {"category": "Supplier Consolidation", "current_cost": 65000, "potential_savings": 15000, 
         "action": "Consolidate suppliers for volume discounts"},
        {"category": "Shipping", "current_cost": 35000, "potential_savings": 12000, 
         "action": "Optimize shipping routes and frequencies"}
    ]
    
    opp_df = pd.DataFrame(opportunities)
    
    # Add savings percentage
    opp_df['savings_percent'] = (opp_df['potential_savings'] / opp_df['current_cost'] * 100).round(1)
    
    # Create horizontal bar chart for savings opportunities
    fig3 = px.bar(
        opp_df,
        y='category',
        x='potential_savings',
        title='Cost-Saving Opportunities',
        labels={'potential_savings': 'Potential Annual Savings ($)', 'category': 'Category'},
        orientation='h',
        text='savings_percent',
        color='savings_percent',
        color_continuous_scale='Blues'
    )
    fig3.update_traces(texttemplate='%{text}%', textposition='outside')
    
    st.plotly_chart(fig3, use_container_width=True)
    
    # Display savings opportunities table
    st.subheader("Savings Opportunities Details")
    st.dataframe(
        opp_df,
        column_config={
            "category": "Category",
            "current_cost": st.column_config.NumberColumn(
                "Current Annual Cost ($)",
                format="$%d"
            ),
            "potential_savings": st.column_config.NumberColumn(
                "Potential Savings ($)",
                format="$%d"
            ),
            "savings_percent": st.column_config.ProgressColumn(
                "% Savings",
                format="%d%%",
                min_value=0,
                max_value=100
            ),
            "action": "Recommended Action"
        },
        use_container_width=True,
        hide_index=True
    )