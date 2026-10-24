import streamlit as st
import pandas as pd
import uuid
from datetime import date

# --- CONFIGURATION ---
st.set_page_config(page_title="Lost & Found Catalog", page_icon="🛍️", layout="wide")

# --- INITIALIZE DATABASE (In-Memory) ---
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=[
        'id', 'report_type', 'item_name', 'category', 'location', 
        'date_reported', 'description', 'status', 'contact', 'image'
    ])

categories = ["Electronics", "Keys", "Wallets/IDs", "Books", "Clothing", "Other"]
locations = ["Library", "Canteen", "Hostel", "Main Block", "Mech Block", "Sports Ground", "Other"]
PLACEHOLDER_IMG = "https://cohenwoodworking.com/wp-content/uploads/2016/09/image-placeholder-500x500.jpg"

# --- CORE FUNCTIONS ---
def add_report(report_type, name, category, location, date_rep, desc, contact, image):
    new_data = {
        'id': str(uuid.uuid4())[:8],
        'report_type': report_type,
        'item_name': name,
        'category': category,
        'location': location,
        'date_reported': pd.to_datetime(date_rep),
        'description': desc,
        'status': 'Open',
        'contact': contact,
        'image': image
    }
    st.session_state.db = pd.concat([st.session_state.db, pd.DataFrame([new_data])], ignore_index=True)

def mark_reunited(item_id):
    st.session_state.db.loc[st.session_state.db['id'] == item_id, 'status'] = 'Returned'

def get_relative_time(reported_date):
    days_diff = (date.today() - reported_date.date()).days
    if days_diff == 0:
        return "Today"
    elif days_diff == 1:
        return "Yesterday"
    else:
        return f"{days_diff} days ago"

# --- SIDEBAR: REPORT AN ITEM ---
with st.sidebar:
    st.header("📝 Report an Item")
    st.markdown("Did you lose or find something? Add it to the catalog here.")
    
    with st.form("report_form", clear_on_submit=True):
        report_type = st.radio("Type", ("Lost", "Found"), horizontal=True)
        item_name = st.text_input("Item Name", placeholder="e.g., Black Wallet")
        uploaded_image = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg"])
        
        category = st.selectbox("Category", categories)
        location = st.selectbox("Location", locations)
        date_rep = st.date_input("Date", value=date.today(), max_value=date.today())
        
        contact = st.text_input("Your Contact (Email/Phone)")
        description = st.text_area("Extra Details (Brand, color, etc.)")
        
        submit = st.form_submit_button("Submit to Catalog", use_container_width=True)
        
        if submit:
            if item_name and contact:
                img_data = uploaded_image.getvalue() if uploaded_image else None
                add_report(report_type, item_name, category, location, date_rep, description, contact, img_data)
                st.success(f"Added {item_name} to the catalog!")
            else:
                st.error("Item Name and Contact Info are required.")

# --- HELPER FUNCTION: DRAW A SHOPPING "CARD" ---
def draw_grid(dataframe):
    if dataframe.empty:
        st.info("No items found matching your criteria.")
        return

    NUM_COLS = 3
    for i in range(0, len(dataframe), NUM_COLS):
        cols = st.columns(NUM_COLS)
        for j in range(NUM_COLS):
            if i + j < len(dataframe):
                row = dataframe.iloc[i + j]
                
                with cols[j]:
                    with st.container(border=True): 
                        # 1. Image
                        if row['image']:
                            st.image(row['image'], use_container_width=True)
                        else:
                            st.image(PLACEHOLDER_IMG, use_container_width=True)
                        
                        # 2. Details
                        st.subheader(row['item_name'])
                        st.markdown(f"📍 **Location:** {row['location']}")
                        
                        time_str = get_relative_time(row['date_reported'])
                        action_word = "Lost" if row['report_type'] == 'Lost' else "Found"
                        st.markdown(f"🕒 **{action_word}:** {time_str}")
                        
                        if row['description']:
                            st.caption(f'"{row["description"]}"')
                            
                        with st.expander("📞 View Contact Info"):
                            st.write(row['contact'])
                        
                        # 3. Action Button
                        if row['status'] == 'Open':
                            if st.button(f"🎉 Mark as Reunited", key=row['id'], use_container_width=True):
                                mark_reunited(row['id'])
                                st.rerun()

# --- HELPER FUNCTION: TAB CONTENT WITH COMPACT FILTER BUTTON ---
def render_tab_content(tab_type, tab_status):
    df = st.session_state.db
    
    if tab_status == 'Returned':
        filtered_df = df[df['status'] == 'Returned']
    else:
        filtered_df = df[(df['report_type'] == tab_type) & (df['status'] == 'Open')]

    col_btn, col_empty = st.columns([1, 4])
    with col_btn:
        with st.popover("⚙️ Filter & Search", use_container_width=True):
            st.markdown("**Filter Options**")
            search_query = st.text_input("Search keywords...", key=f"search_{tab_type}_{tab_status}")
            selected_cat = st.selectbox("Category", ["All"] + categories, key=f"cat_{tab_type}_{tab_status}")

    if search_query:
        filtered_df = filtered_df[
            filtered_df['item_name'].str.contains(search_query, case=False, na=False) |
            filtered_df['description'].str.contains(search_query, case=False, na=False)
        ]
    if selected_cat != "All":
        filtered_df = filtered_df[filtered_df['category'] == selected_cat]

    draw_grid(filtered_df)

# --- MAIN UI: THE CATALOG ---
st.title("🛍️ BMSCE Lost & Found Catalog")

# 4 TABS: Added Campus Stats
tab_lost, tab_found, tab_reunited, tab_stats = st.tabs([
    "🔴 Lost Items", 
    "🟢 Found Items", 
    "🤝 Reunited (Resolved)", 
    "📊 Campus Stats"
])

with tab_lost:
    st.header("Currently Lost")
    render_tab_content(tab_type="Lost", tab_status="Open")

with tab_found:
    st.header("Currently Found")
    render_tab_content(tab_type="Found", tab_status="Open")

with tab_reunited:
    st.header("Successfully Reunited!")
    st.markdown("These items were lost, but have been safely returned to their owners.")
    render_tab_content(tab_type="Both", tab_status="Returned")

# --- NEW TAB: CAMPUS STATISTICAL ANALYSIS ---
with tab_stats:
    st.header("📊 Lost & Found Campus Insights")
    df = st.session_state.db
    
    lost_df = df[df['report_type'] == 'Lost']
    
    if not lost_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Most Commonly Lost Categories")
            st.markdown("Distribution of reported lost items by category:")
            category_counts = lost_df['category'].value_counts()
            st.bar_chart(category_counts)
            
        with col2:
            st.subheader("Top Campus Hotspots")
            st.markdown("Locations where items are most frequently misplaced:")
            location_counts = lost_df['location'].value_counts()
            st.bar_chart(location_counts)

        st.divider()
        st.metric(label="Total Items Successfully Reunited", value=len(df[df['status'] == 'Returned']))
    else:
        st.info("No reported lost items in the database yet. Add some items from the sidebar to view live analytics!")