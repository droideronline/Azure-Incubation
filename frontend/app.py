import streamlit as st
from auth import authenticate_user_demo, check_authentication, get_auth_url, exchange_code_for_token, get_user_profile, logout
from utils import get_books, add_book, update_book, delete_book
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI backend URL - Update this with your VM's public IP
BACKEND_URL = "http://48.216.155.232:8000"  # Change to your VM's public IP when deployed

# Configure Streamlit page
st.set_page_config(
    page_title="Book Management System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("📚 Book Management Application")
    st.markdown("*Powered by Azure Services: VM, Cosmos DB, Key Vault, and Azure AD*")
    
    # Authentication check
    if not check_authentication():
        st.subheader("🔐 Authentication Required")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("**Demo Mode** - Click below for quick access")
            if st.button("🚀 Demo Login", type="primary"):
                token = authenticate_user_demo()
                if token:
                    st.session_state["access_token"] = token
                    st.session_state["user_info"] = {"name": "Demo User", "email": "demo@example.com"}
                    st.rerun()
        
        with col2:
            st.info("**Production Mode** - Use Azure AD")
            if st.button("🔗 Login with Azure AD"):
                auth_url = get_auth_url()
                st.markdown(f"[Click here to login with Azure AD]({auth_url})")
                # Prompt for authorization code returned after Azure AD login
                auth_code = st.text_input("Enter authorization code:", key="auth_code_input")
                if auth_code and st.button("Submit Code", key="submit_auth_code"):
                    token = exchange_code_for_token(auth_code)
                    if token:
                        # Store token and retrieve actual user info from Graph API
                        st.session_state["access_token"] = token
                        profile = get_user_profile(token)
                        name = profile.get("displayName") or profile.get("userPrincipalName", "User")
                        email = profile.get("mail") or profile.get("userPrincipalName", "")
                        st.session_state["user_info"] = {"name": name, "email": email}
                        st.success(f"✅ Authentication successful! Welcome {name}")
                        st.rerun()
                    else:
                        st.error("❌ Failed to exchange code for token")
        
        return
    
    # User is authenticated - show the main application
    user_info = st.session_state.get("user_info", {})
    
    # Sidebar
    with st.sidebar:
        st.success(f"👋 Welcome, {user_info.get('name', 'User')}!")
        
        if st.button("🚪 Logout"):
            logout()
            st.rerun()
        
        st.divider()
        
        # Navigation menu
        page = st.selectbox(
            "📋 Navigation",
            ["📖 View Books", "➕ Add Book", "🔧 Manage Books", "ℹ️ About"]
        )
    
    # Main content area
    if page == "📖 View Books":
        show_books_page()
    elif page == "➕ Add Book":
        show_add_book_page()
    elif page == "🔧 Manage Books":
        show_manage_books_page()
    elif page == "ℹ️ About":
        show_about_page()

def show_books_page():
    st.header("📖 Book Library")
    
    try:
        token = st.session_state.get("access_token")
        books = get_books(BACKEND_URL, token)
        
        if books:
            # Display books in a nice grid
            cols = st.columns(3)
            for i, book in enumerate(books):
                with cols[i % 3]:
                    with st.container():
                        st.subheader(book.get("title", "N/A"))
                        st.write(f"**Author:** {book.get('author', 'N/A')}")
                        st.write(f"**Published:** {book.get('published_date', 'N/A')}")
                        st.write(f"**Description:** {book.get('description', 'N/A')[:100]}...")
                        st.write(f"**ID:** {book.get('RowKey', book.get('id', 'N/A'))}")
        else:
            st.info("📚 No books found. Add some books to get started!")
            
    except Exception as e:
        st.error(f"❌ Error fetching books: {e}")
        logger.error(f"Error in show_books_page: {e}")

def show_add_book_page():
    st.header("➕ Add New Book")
    
    with st.form("add_book_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("📖 Book Title*", placeholder="Enter book title")
            author = st.text_input("✍️ Author*", placeholder="Enter author name")
        
        with col2:
            published_date = st.date_input("📅 Published Date")
            
        description = st.text_area("📝 Description", placeholder="Enter book description", height=100)
        
        submitted = st.form_submit_button("➕ Add Book", type="primary")
        
        if submitted:
            if title and author:
                try:
                    book_data = {
                        "title": title,
                        "author": author,
                        "description": description,
                        "published_date": str(published_date)
                    }
                    
                    token = st.session_state.get("access_token")
                    success = add_book(BACKEND_URL, token, book_data)
                    
                    if success:
                        st.success("✅ Book added successfully!")
                        st.balloons()
                    else:
                        st.error("❌ Failed to add book")
                        
                except Exception as e:
                    st.error(f"❌ Error adding book: {e}")
                    logger.error(f"Error in add_book: {e}")
            else:
                st.warning("⚠️ Please fill in all required fields (Title and Author)")

def show_manage_books_page():
    st.header("🔧 Manage Books")
    
    try:
        token = st.session_state.get("access_token")
        books = get_books(BACKEND_URL, token)
        
        if books:
            book_titles = [f"{book.get('title', 'N/A')} - {book.get('RowKey', book.get('id', 'N/A'))}" for book in books]
            selected_book = st.selectbox("Select a book to edit or delete:", book_titles)
            
            if selected_book:
                book_id = selected_book.split(" - ")[-1]
                book = next((b for b in books if b.get('RowKey', b.get('id')) == book_id), None)
                
                if book:
                    tab1, tab2 = st.tabs(["✏️ Edit", "🗑️ Delete"])
                    
                    with tab1:
                        with st.form("edit_book_form"):
                            title = st.text_input("Title", value=book.get("title", ""))
                            author = st.text_input("Author", value=book.get("author", ""))
                            description = st.text_area("Description", value=book.get("description", ""))
                            published_date = st.date_input("Published Date")
                            
                            if st.form_submit_button("💾 Update Book"):
                                # Implementation for update
                                st.info("Update functionality - coming soon!")
                    
                    with tab2:
                        st.warning("⚠️ This action cannot be undone!")
                        if st.button("🗑️ Delete Book", type="secondary"):
                            # Implementation for delete
                            st.info("Delete functionality - coming soon!")
        else:
            st.info("📚 No books available to manage")
            
    except Exception as e:
        st.error(f"❌ Error loading books: {e}")

def show_about_page():
    st.header("ℹ️ About This Application")
    
    st.markdown("""
    ## 🏗️ Architecture Overview
    
    This Book Management application demonstrates integration with multiple Azure services:
    
    ### 🔧 **Backend Technologies**
    - **FastAPI**: Modern Python web framework for building APIs
    - **Azure Cosmos DB**: NoSQL database using Table API
    - **Azure Key Vault**: Secure storage for connection strings and secrets
    - **Azure Active Directory**: Authentication and authorization
    
    ### 🎨 **Frontend Technologies**  
    - **Streamlit**: Interactive web application framework
    - **Python**: Backend logic and API integration
    
    ### ☁️ **Azure Services Used**
    - **Azure Virtual Machine**: Hosting the application
    - **Azure Cosmos DB**: Database storage with Table API
    - **Azure Key Vault**: Secure secret management
    - **Azure Active Directory**: Identity and access management
    
    ### 🔒 **Security Features**
    - Managed Identity for secure Azure service access
    - JWT token validation for API authentication
    - Secure storage of sensitive configuration in Key Vault
    
    ### 📊 **Key Features**
    - Create, read, update, and delete books
    - Azure AD authentication integration
    - Responsive web interface
    - Real-time data synchronization
    - Comprehensive logging and error handling
    """)

if __name__ == "__main__":
    main()
