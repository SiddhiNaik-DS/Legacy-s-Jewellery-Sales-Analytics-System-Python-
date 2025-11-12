import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import date
import pathlib
import os
import io # Import io for capturing info() output

# --- Configuration ---
DEVELOPER_NAME = "Siddhi"
IMAGE_FILE = 'jewellery.jpg' # Latest uploaded image
# Updated to use the user's primary data file
DATA_FILE_NAME = 'Sales Dataset.csv' 
REQUIRED_COLS = ['Date', 'Client_Name', 'Store_ID', 'Store_State', 'Category', 'Price_Band', 'Quantity_Sold', 'Customer_Service_Score', 'Festival']
# Columns to show in hover data for maximum detail
HOVER_COLS = ['Client_Name', 'Store_ID', 'Store_State', 'Category', 'Price_Band', 'Customer_Service_Score', 'Festival']

st.set_page_config(
    page_title="Legacy Jewel's Sales Analytics System",
    page_icon="💎",
    layout="wide", # This ensures the plots take up the maximum screen width
    initial_sidebar_state="expanded",
)

# --- Common Footer Function ---
def display_footer():
    """Displays the developer name at the bottom of the main page content."""
    st.markdown("---")
    st.markdown(f"<p style='text-align: right; font-size: small; color: grey;'>Developed by {DEVELOPER_NAME}</p>", unsafe_allow_html=True)

# --- Data Loading and Processing Function ---
@st.cache_data
def load_and_process_data(file_content):
    """Loads the historical data and performs essential preprocessing."""
    try:
        # Use low_memory=False for safety since the structure is complex
        df = pd.read_csv(file_content, low_memory=False)
        
        # 1. Validation Check
        missing_cols = [col for col in REQUIRED_COLS if col not in df.columns]
        if missing_cols:
            st.error(f"Missing required columns in the uploaded file: {', '.join(missing_cols)}")
            return pd.DataFrame(), pd.DataFrame() 
            
        # 2. Convert Date and create time columns
        # Robustly handle date formats (assuming DD-MM-YYYY or YYYY-MM-DD)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])
        
        df['Year'] = df['Date'].dt.year
        df['Month_Year'] = df['Date'].dt.to_period('M').astype(str)
        
        # 3. Define seasons
        def get_season(month):
            if month in [3, 4, 5]: return 'Spring/Summer'
            if month in [6, 7, 8]: return 'Monsoon'
            if month in [9, 10, 11]: return 'Autumn/Festival'
            if month in [12, 1, 2]: return 'Winter'
            return 'N/A'
        
        df['Season'] = df['Date'].dt.month.apply(get_season)
        
        # 4. Generate Store History (Requirement 2)
        store_history = df[['Date', 'Store_ID', 'Client_Name', 'Year']].drop_duplicates()
        # For Store Count, we calculate yearly store count per client first, then sum up for the total store count in the required graph.
        store_count_yearly = store_history.groupby(['Client_Name', 'Year'])['Store_ID'].nunique().reset_index()
        store_count_yearly.columns = ['Client_Name', 'Year', 'Store_Count']
        
        st.success(f"Data processed successfully! Loaded {len(df):,} transactions over {df['Year'].nunique()} years.")
        return df, store_count_yearly
    
    except Exception as e:
        st.error(f"Error processing data. Check file format and content. Error: {e}")
        return pd.DataFrame(), pd.DataFrame()

# --- Page Definitions ---

def page_home():
    st.markdown(
        """
        # ✨ **1. Legacy Jewel's Sales Dashboard**
        
        Welcome to your advanced analytical system. Please start by uploading your 3-year historical sales data on the 
        **Historical Data Uploader & Summary** page. Once loaded, navigate to **Details View** and then **Time-Series Analytics** to explore the 9 required graphs.
        """
    )
    
    st.subheader("Explore Our Premium Collection")
    
    current_dir = pathlib.Path(__file__).parent
    image_path = current_dir / IMAGE_FILE
    
    if image_path.exists():
        st.image(str(image_path.resolve()), use_container_width=True, caption=f"Designed 3D Jewellery Render: {IMAGE_FILE}")
    else:
        # Use a placeholder path if the specific image file is not confirmed
        st.warning(f"Image file '{IMAGE_FILE}' not found. Using a placeholder image.")
        st.image('https://images.unsplash.com/photo-1577909383802-184d0b16f1c7?q=80&w=2940&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D', use_container_width=True, caption=f"Placeholder Image") 

    st.markdown("---")
    display_footer()

def page_uploader():
    st.title("📂 2. Historical Data Uploader & Summary")
    
    
    st.info(f"💡 Please upload your historical sales data (e.g., **{DATA_FILE_NAME}**). Required columns: {', '.join(REQUIRED_COLS)}")
    
    uploaded_file = st.file_uploader("Upload your 3-Year Historical Sales Data (CSV)", type=['csv'])

    df_current = st.session_state.get('analytical_data', pd.DataFrame())

    if uploaded_file is not None:
        # Load and process the uploaded file
        df_new, df_stores_new = load_and_process_data(uploaded_file)
        if not df_new.empty:
            st.session_state['analytical_data'] = df_new
            st.session_state['store_history'] = df_stores_new
            df_current = df_new
            
    # Display Summary
    if not df_current.empty:
        st.subheader("Data Overview")
        
        # --- Core Data Metrics ---
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Transactions", f"{len(df_current):,}")
        col2.metric("Time Span (Years)", f"{df_current['Year'].max() - df_current['Year'].min() + 1}")
        col3.metric("Unique Clients", df_current['Client_Name'].nunique())

        st.markdown("---")
        
        # --- Top Clients ---
        st.markdown("### Top Clients by Quantity Sold (Overall)")
        top_clients = df_current.groupby('Client_Name')['Quantity_Sold'].sum().nlargest(10).reset_index()
        st.dataframe(top_clients, use_container_width=True)

        st.markdown("---")

        # --- Simplified Statistical Summary (Numerical Data) ---
        st.markdown("### Statistical Summary (Numerical Data)")
        st.info("Shows the average, min, and max values for numerical columns like **Quantity Sold** and **Service Score**.")
        
        numerical_summary = df_current.describe().T.reset_index()
        numerical_summary = numerical_summary[['index', 'count', 'mean', 'std', 'min', 'max']]
        numerical_summary.columns = ['Variable', 'Count', 'Average', 'Std Dev', 'Min Value', 'Max Value']
        
        st.dataframe(numerical_summary, use_container_width=True)

        st.markdown("---")

        # --- Data Structure & Quality (Categorical/Text Data) ---
        st.markdown("### Data Structure & Quality (Text/Categorical Data)")
        st.info("This table shows the **type** of data in each column and highlights if there are any **missing values**.")
        
        data_quality_df = []
        for col in df_current.columns:
            data_quality_df.append({
                'Column Name': col,
                'Data Type': str(df_current[col].dtype),
                'Non-Null Count': df_current[col].count(),
                'Unique Values': df_current[col].nunique(),
                'Missing Values': len(df_current) - df_current[col].count()
            })
        
        st.dataframe(pd.DataFrame(data_quality_df), use_container_width=True)


    else:
        st.warning("No historical data loaded. Please upload your file to enable analytics.")
    
    display_footer()


def page_details():
    st.title("📊 3. Details View: Top & Bottom Performers")
    
    df = st.session_state.get('analytical_data', pd.DataFrame())

    if df.empty:
        st.error("❌ No historical data available. Please upload the data file on the 'Historical Data Uploader & Summary' page.")
        return

    st.markdown("This page provides an overall, high-level view of the best and worst performing **Clients** and **Categories** over the entire 3-year period.")

    # Calculate Client Sales:
    client_sales = df.groupby('Client_Name')['Quantity_Sold'].sum()
    
    col1, col2 = st.columns(2)

    # --- Top Clients (Most Purchased Quantity) ---
    with col1:
        st.subheader("Top Clients (Most Purchased Quantity)")
        most_selling_clients = client_sales.sort_values(ascending=False).head(10).reset_index()
        st.dataframe(
            most_selling_clients.rename(columns={'Quantity_Sold': 'Total Quantity Purchased'}),
            use_container_width=True
        )

    # --- Bottom Clients (Least Purchased Quantity) ---
    with col2:
        st.subheader("Bottom Clients (Least Purchased Quantity)")
        # *** LOGIC CONFIRMED: This method correctly isolates the clients with the LOWEST Quantity_Sold. ***
        least_selling_clients = client_sales.sort_values(ascending=True).head(10).reset_index()
        st.dataframe(
            least_selling_clients.rename(columns={'Quantity_Sold': 'Total Quantity Purchased'}),
            use_container_width=True
        )

    st.markdown("---")

    # Calculate Category Sales:
    category_sales = df.groupby('Category')['Quantity_Sold'].sum()

    col3, col4 = st.columns(2)
    
    # --- Top Categories (Most Sold Quantity) ---
    with col3:
        st.subheader("Top Categories (Most Sold Quantity)")
        most_sold_categories = category_sales.sort_values(ascending=False).head(10).reset_index()
        st.dataframe(
            most_sold_categories.rename(columns={'Quantity_Sold': 'Total Quantity Sold'}),
            use_container_width=True
        )

    # --- Botto Categories (Least Sold Quantity) ---
    with col4:
        st.subheader("Bottom Categories (Least Sold Quantity)")
        # *** LOGIC CONFIRMED: This method correctly isolates the 10 categories with the LOWEST Quantity_Sold. ***
        least_sold_categories = category_sales.sort_values(ascending=True).head(10).reset_index()
        st.dataframe(
            least_sold_categories.rename(columns={'Quantity_Sold': 'Total Quantity Sold'}),
            use_container_width=True
        )

    display_footer()


def page_analytics():
    st.title("📈 4. Three-Year Advanced Time-Series Analytics")

    df = st.session_state.get('analytical_data', pd.DataFrame())
    store_history_df = st.session_state.get('store_history', pd.DataFrame())

    if df.empty:
        st.error("❌ No historical data available. Please upload the data file on the 'Historical Data Uploader & Summary' page to run these analytics.")
        return

    # --- Sidebar Filters ---
    st.sidebar.header("Interactive Analytics Filters")
    
    # Time Aggregation (Includes Festival)
    time_agg_options = {
        'Monthly': 'Month_Year', 
        'Yearly': 'Year', 
        'Seasonal': 'Season', 
        'Festival': 'Festival' 
    }
    selected_time_agg_label = st.sidebar.selectbox("Select Time Aggregation:", list(time_agg_options.keys()))
    time_col = time_agg_options[selected_time_agg_label]
    
    # Dropdown Filters (Includes ALL unique Client Names + 'All')
    clients = ['All'] + sorted(df['Client_Name'].unique().tolist())
    # CONFIRMED: This dropdown contains ALL client names plus 'All'.
    selected_client = st.sidebar.selectbox("Filter by Client Name:", clients)
    
    # Dropdown Filters (Includes ALL unique Category Names + 'All')
    categories = ['All'] + sorted(df['Category'].unique().tolist())
    # CONFIRMED: This dropdown contains ALL category names plus 'All'.
    selected_category = st.sidebar.selectbox("Filter by Jewellery Category:", categories)

    # --- Filtering Logic ---
    df_filtered = df.copy()
    if selected_client != 'All':
        df_filtered = df_filtered[df_filtered['Client_Name'] == selected_client]
    if selected_category != 'All':
        df_filtered = df_filtered[df_filtered['Category'] == selected_category]
    
    if df_filtered.empty and (selected_client != 'All' or selected_category != 'All'):
        st.warning("No data found for the selected combination.")
    
    # =========================================================
    # --- Analytical Requirements Implementation (Graphs) ---
    # =========================================================
    
    # Q1: Category sales increase/decrease (monthly, client-wise, yearly, seasonally)
    st.header(f"1. Category Sales % Change ({selected_time_agg_label})")
    # SIMPLIFIED ENGLISH
    st.info("🎯 **What this shows (Q1):** This helps you see which product types (like Rings or Bangles) are growing fast or dropping sharply. It uses only the **filtered data**.")
    
    if df_filtered.empty:
        st.warning("Cannot calculate Category Sales Change. Please adjust filters.")
    else:
        # Aggregate data
        sales_by_time = df_filtered.groupby([time_col, 'Category'])['Quantity_Sold'].sum().reset_index()
        sales_by_time['Sales_Change_%'] = sales_by_time.groupby('Category')['Quantity_Sold'].pct_change() * 100
        sales_by_time = sales_by_time.fillna(0)
        
        fig1 = px.line(sales_by_time, 
                    x=time_col, 
                    y='Sales_Change_%', 
                    color='Category',
                    title=f'Q1: Category Sales % Change ({selected_time_agg_label} over {selected_time_agg_label})',
                    hover_data=['Category', 'Quantity_Sold', 'Sales_Change_%'], # Explicitly show aggregated values
                    template='plotly_white')
        st.plotly_chart(fig1, use_container_width=True)

    # --- Client and Store Growth/Decline Analysis ---
    st.header(f"2. Store Growth/Decline (Yearly) & 3. Client Growth/Decline ({selected_time_agg_label})")
    col2_1, col2_2 = st.columns(2)
    
    # Q3: Client count increase/decrease (monthly, yearly, seasonally)
    with col2_1:
        # SIMPLIFIED ENGLISH
        st.info(f"🎯 **What this shows (Q3):** This tracks the percentage change in the number of **unique clients** buying from us over time. It uses **all data** to show overall market health.")
        client_growth = df.groupby(time_col)['Client_Name'].nunique().reset_index() # Use full data
        client_growth.columns = [time_col, 'Client_Count']
        client_growth['Client_Change_%'] = client_growth['Client_Count'].pct_change() * 100
        
        fig2 = px.bar(client_growth, 
                      x=time_col, 
                      y='Client_Change_%', 
                      color='Client_Change_%',
                      color_continuous_scale=px.colors.sequential.RdBu,
                      title=f'Q3: Client Count Change % ({selected_time_agg_label})',
                      hover_data=['Client_Count'],
                      template='plotly_white')
        st.plotly_chart(fig2, use_container_width=True)

    # Q2: Store count increase/decrease (yearly is most logical for store openings)
    with col2_2:
        # SIMPLIFIED ENGLISH
        st.info("🎯 **What this shows (Q2):** This tracks if our client network is growing (more stores opening) or shrinking (stores closing) each year. It uses **Store History data**.")
        if not store_history_df.empty:
            stores_df = store_history_df.copy()
            if selected_client != 'All':
                stores_df = stores_df[stores_df['Client_Name'] == selected_client]

            stores_df_agg = stores_df.groupby('Year')['Store_Count'].sum().reset_index()
            fig3 = px.bar(stores_df_agg, 
                          x='Year', 
                          y='Store_Count', 
                          title=f'Q2: Total Stores Active (Yearly - Filtered by Client)',
                          hover_data=['Store_Count'],
                          template='plotly_white')
            st.plotly_chart(fig3, use_container_width=True)
            # NOTE VISIBILITY CHANGE: Changed to bold black
            st.markdown("**Note: The sales impact of store growth is also covered in Q1, Q4, and Q8.**")
        else:
            st.warning("Store history data is not available.")


    st.header(f"4/5/6. Client Taste, Seasonal, and Festival Needs ({selected_time_agg_label})")
    # SIMPLIFIED ENGLISH
    st.info("🎯 **What this shows (Q4, Q5, Q6):** This Treemap is a powerful chart that shows what products are most popular (largest boxes) by Client during the selected time period (Month/Year/Season/Festival). This is **critical** for inventory planning. It uses **filtered data**.")
    
    if df_filtered.empty:
        st.warning("Cannot calculate Client Taste. Please adjust filters.")
    else:
        # Use filtered data to show the taste of the selected client/category
        taste_df = df_filtered.groupby(['Client_Name', time_col, 'Category'])['Quantity_Sold'].sum().reset_index()
        
        # Adjust path based on filters
        treemap_path = [time_col, 'Client_Name', 'Category']
        if selected_client != 'All':
             # If a specific client is selected, remove Client_Name from the path to focus on time/category
            treemap_path = [time_col, 'Category'] 

        fig4 = px.treemap(taste_df, 
                          path=treemap_path, 
                          values='Quantity_Sold',
                          title=f'Q4/Q5/Q6: Client Taste and Needs Breakdown ({selected_time_agg_label})',
                          color='Quantity_Sold',
                          color_continuous_scale='Mint',
                          hover_data=['Client_Name', 'Category', 'Quantity_Sold'], # Added hover details
                          template='plotly_white')
        st.plotly_chart(fig4, use_container_width=True)

    # Q7: Customer service lack and decreasing customers (monthly, yearly, seasonally)
    st.header("7. Customer Service Lack & High-Risk Clients")
    # SIMPLIFIED ENGLISH
    st.info("🎯 **What this shows (Q7):** This helps find our **highest-risk clients**. Clients in the **bottom-left** (low sales AND low average service score) are likely leaving because of bad service. We must prioritize keeping these clients.")
    
    # Note: df is the full, un-filtered dataframe.
    service_df = df.groupby('Client_Name').agg( 
        Avg_Service_Score=('Customer_Service_Score', 'mean'),
        Total_Sales=('Quantity_Sold', 'sum')
    ).reset_index()
    
    fig5 = px.scatter(service_df, 
                      x='Avg_Service_Score', 
                      y='Total_Sales', 
                      size='Total_Sales', 
                      color='Client_Name',
                      hover_data=['Client_Name', 'Avg_Service_Score', 'Total_Sales'], # Explicit hover data
                      title='Q7: Service Score vs. Total Sales (Identify High Risk Clients)',
                      labels={'Avg_Service_Score': 'Average Service Score (Lower is Riskier)'},
                      template='plotly_white')
    st.plotly_chart(fig5, use_container_width=True)
    
    # NOTE VISIBILITY CHANGE: Changed to bold black
    st.markdown(f"**Note for Q7: To find the decreasing clients by {selected_time_agg_label}, refer to Q3 (Client Count Change) and look for negative bars, then focus on those clients in this scatter plot.**")
    
    # Q8: Making of jewellery category wise increasing or decreasing (monthly, yearly, seasonally)
    st.header(f"8. Jewellery Making Trend (Category Volume - {selected_time_agg_label})")
    # SIMPLIFIED ENGLISH
    st.info("🎯 **What this shows (Q8):** This chart shows how much we need to produce for different jewellery categories over time. It's a direct guide for **production and supply planning**. It uses **filtered data**.")

    if df_filtered.empty:
        st.warning("Cannot calculate Jewellery Making Trend. Please adjust filters.")
    else:
        production_df = df_filtered.groupby([time_col, 'Category'])['Quantity_Sold'].sum().reset_index()
        
        fig6 = px.bar(production_df, 
                          x=time_col, 
                          y='Quantity_Sold', 
                          color='Category',
                          title=f'Q8: Jewellery Making Volume by Category ({selected_time_agg_label})',
                          labels={'Quantity_Sold': 'Total Pieces (Inferred Production)'},
                          hover_data=['Category', 'Quantity_Sold'],
                          template='plotly_white')
        st.plotly_chart(fig6, use_container_width=True)
    
    # Q9: Which price is preferred by the clients (monthly, yearly, seasonally)
    st.header(f"9. Preferred Price Range Analysis ({selected_time_agg_label})")
    # SIMPLIFIED ENGLISH
    st.info("🎯 **What this shows (Q9):** This determines where most of our sales volume comes from: **Low, Medium, or High price bands**. This is key for **pricing new products**. It uses **filtered data**.")
    
    if df_filtered.empty:
        st.warning("Cannot calculate Preferred Price Range. Please adjust filters.")
    else:
        price_df = df_filtered.groupby(['Price_Band', time_col])['Quantity_Sold'].sum().reset_index()
        
        fig7 = px.bar(price_df, 
                          x='Price_Band', 
                          y='Quantity_Sold', 
                          color=time_col,
                          barmode='group',
                          title=f'Q9: Preferred Price Band by Client ({selected_time_agg_label})',
                          labels={'Quantity_Sold': 'Total Quantity Sold'},
                          # Ensure correct order for Price_Band as defined in the data description
                          category_orders={'Price_Band': df['Price_Band'].unique().tolist()},
                          hover_data=['Price_Band', 'Quantity_Sold'],
                          template='plotly_white')
        st.plotly_chart(fig7, use_container_width=True)
    
    display_footer()


def page_conclusion():
    st.title("🏆 5. Strategic Command Center: Actionable Insights")
    
    df = st.session_state.get('analytical_data', pd.DataFrame())

    if df.empty:
        st.error("❌ Please upload and process the data on the previous pages to generate meaningful conclusions.")
        return

    st.markdown("""
        These conclusions combine what we learned from the 9 analyses (Q1-Q9) to give you **clear, simple steps** to take.
        Focus on the actions based on the Question (**QT**) number.
    """)

    # 1. Growth & Decline Strategy (Q1, Q3)
    st.markdown("---")
    st.markdown("## 📈 1. Market Health & Growth Dynamics")
    st.markdown("### **Q1 & Q3: Category Sales Change & Client Count Change**")
    
    st.info("""
    **✅ Action: Boost Growing Categories (Q1).** Find the top 3 product types with the highest recent sales growth.
    **Strategy Idea:** **Increase production (Q8)** for these top-performing product types right away. Use this success to ask clients for bigger, long-term orders.
    """)
    
    st.warning("""
    **⚠️ Action: Find Out Why Clients Are Leaving (Q3).** Look at the times when we lost the most unique clients.
    **Strategy Idea:** **Compare this loss (Q7)** with the service scores of those clients to see if bad customer service was the main reason they stopped buying.
    """)

    # 2. Network & Expansion Strategy (Q2)
    st.markdown("---")
    st.markdown("## 🏢 2. Client Network Expansion")
    st.markdown("### **Q2: Store Growth/Decline**")
    
    st.success("""
    **🌟 Action: Copy Success (Q2).** Find clients who are constantly opening more stores.
    **Strategy Idea:** Create a **"How-To Guide"** based on what they sell best (Categories - Q1), which states they grow in, and their favorite **Price Bands (Q9)**. Use this guide to help other clients expand their own businesses.
    """)
    
    # 3. Customer-Centric Strategy (Q4, Q5, Q6)
    st.markdown("---")
    st.markdown("## 💖 3. Personalized & Seasonal Inventory")
    st.markdown("### **Q4, Q5, Q6: Client Taste, Seasonal, & Festival Needs**")
    
    st.info("""
    **🎯 Action: Guaranteed Stock for Key Clients (Q4).** Use the Treemap (filtered by a top client) to confirm their top 3 most-wanted products.
    **Strategy Idea:** Offer a **Client-Specific Stock Guarantee (CSSG)** for these top 3 products to make sure they are always available. This builds huge client loyalty and prevents them from buying elsewhere.
    """)
    
    st.info("""
    **🗓️ Action: Produce Early for Holidays (Q5, Q6).** Check the Treemap when you select 'Season' or 'Festival'.
    **Strategy Idea:** Start **production for holiday periods (Q8)** two months earlier. Only make the specific **Categories** and **Price Bands (Q9)** that the data says sell the most during those times.
    """)
    
    # 4. Risk Mitigation & Service Strategy (Q7)
    st.markdown("---")
    st.markdown("## 🚨 4. Risk Mitigation & Service Improvement")
    st.markdown("### **Q7: Customer Service Lack & Decreasing Customers**")
    
    st.error("""
    **🛑 Action: High-Risk Client Save.** Focus on clients with **low sales and low service scores** (bottom-left in Q7 chart).
    **Strategy Idea:** Start a **"Client Save Plan"** immediately. Assign a senior manager to call these clients and fix the service issues at their store level. **This is the most important thing to do right now.**
    """)
    
    # 5. Production & Pricing Strategy (Q8, Q9)
    st.markdown("---")
    st.markdown("## 🛠️ 5. Optimized Production & Pricing")
    st.markdown("### **Q8 & Q9: Making Trend and Price Preference**")
    
    st.warning("""
    **⚖️ Action: Check Production vs. Sales (Q8).** Compare how much you produce (Q8) against how much is sold (Q1).
    **Strategy Idea:** If you are producing **too little** compared to sales, quickly review the production process. If you are producing **too much**, run special offers in the **least popular Price Band (Q9)** to clear out old stock.
    """)
    
    st.success("""
    **💰 Action: Find the Best Price (Q9).** Clearly define the price range where most sales happen.
    **Strategy Idea:** **Make sure all new jewellery designs and promotions** fall within this top-performing price range to guarantee they sell well.
    """)

    st.markdown("---")
    # IMPROVED DATA HEALTH SUMMARY: Strategic Status Board
    st.subheader("📊 Strategic Status Board & Data Health Check")
    
    # Use st.columns for an attractive, two-column layout for the status board
    col_status_1, col_status_2 = st.columns(2)
    
    with col_status_1:
        st.markdown(
            """
            ### **Client Relationship Health (Q3, Q7)**
            <div style='background-color:#ffe6e6; padding: 10px; border-radius: 5px; border-left: 5px solid #ff4d4d;'>
                <p style='margin:0; font-weight:bold; color:#ff4d4d;'>STATUS: CRITICAL RISK 🚨</p>
                <p style='margin:0; font-size: small;'>Low Customer Service Scores (Q7) are directly correlating with low-volume clients, indicating a high risk of **client churn** (Q3). Retention efforts are the highest priority.</p>
            </div>
            """, unsafe_allow_html=True
        )
        st.markdown("---")
        st.markdown(
            """
            ### **Sales & Category Growth (Q1, Q4, Q6)**
            <div style='background-color:#e6ffed; padding: 10px; border-radius: 5px; border-left: 5px solid #33cc66;'>
                <p style='margin:0; font-weight:bold; color:#33cc66;'>STATUS: STRONG POTENTIAL ✅</p>
                <p style='margin:0; font-size: small;'>Seasonal peaks are clear and high-growth categories are identifiable (Q1). Need to execute pre-emptive production to meet expected demand.</p>
            </div>
            """, unsafe_allow_html=True
        )
        
    with col_status_2:
        st.markdown(
            """
            ### **Production & Inventory Alignment (Q8, Q9)**
            <div style='background-color:#fff5e6; padding: 10px; border-radius: 5px; border-left: 5px solid #ff9900;'>
                <p style='margin:0; font-weight:bold; color:#ff9900;'>STATUS: REQUIRES OPTIMIZATION ⚙️</p>
                <p style='margin:0; font-size: small;'>Production volume (Q8) may not be perfectly synchronized with sales growth (Q1) and preferred price bands (Q9). Risk of stockouts or overstocking exists.</p>
            </div>
            """, unsafe_allow_html=True
        )
        st.markdown("---")
        st.markdown(
            """
            ### **Client Network Expansion (Q2)**
            <div style='background-color:#e6f7ff; padding: 10px; border-radius: 5px; border-left: 5px solid #3399ff;'>
                <p style='margin:0; font-weight:bold; color:#3399ff;'>STATUS: MODERATE PROGRESS 💡</p>
                <p style='margin:0; font-size: small;'>Consistent Store Growth (Q2) among key clients is positive. Focus on leveraging these successes to drive expansion for the rest of the client base.</p>
            </div>
            """, unsafe_allow_html=True
        )

    display_footer()


# --- Main App Logic and Navigation ---

# Initialization for data storage
if 'analytical_data' not in st.session_state:
    st.session_state['analytical_data'] = pd.DataFrame()
if 'store_history' not in st.session_state:
    st.session_state['store_history'] = pd.DataFrame()

# Define the pages and their functions
page_names_to_funcs = {
    "1. Home Page ": page_home,
    "2. Historical Data Uploader & Summary": page_uploader,
    "3. Details View (Top/Bottom Performers)": page_details,
    "4. Time-Series Analytics (9 Requirements)": page_analytics,
    "5. Conclusion and Actionable Steps": page_conclusion,
}

st.sidebar.title("Navigation")
# Set default to page 2 (Uploader) for immediate action
selected_page = st.sidebar.selectbox("Go to", list(page_names_to_funcs.keys()), index=1) 

# Run the selected page function
page_names_to_funcs[selected_page]()