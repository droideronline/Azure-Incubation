import streamlit as st
from auth import authenticate_user_demo, check_authentication, get_auth_url, exchange_code_for_token, get_user_profile, logout
from utils import get_books, add_book, update_book, delete_book
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
BACKEND_URL = "http://localhost:8000"  # This will be updated by setup script
VIEW_BOOKS_PAGE = "📖 View Books"
ADD_BOOK_PAGE = "➕ Add Book"
MANAGE_BOOKS_PAGE = "🔧 Manage Books"
ABOUT_PAGE = "ℹ️ About"

# Configure Streamlit page
st.set_page_config(
    page_title="Book Management System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

def handle_demo_login():
    """Handle demo login process"""
    if st.button("🚀 Demo Login", key="demo_login_button"):
        token = authenticate_user_demo()
        st.session_state["access_token"] = token
        st.session_state["user_info"] = {"name": "Demo User", "email": "demo@example.com"}
        st.rerun()

def handle_production_login():
    """Handle production Azure AD login process"""
    auth_url = get_auth_url()
    st.markdown(f"**Step 1:** [Click here to login with Azure AD]({auth_url})")
    st.markdown("**Step 2:** Copy the authorization code from the URL after authentication")
    st.markdown("**Step 3:** Paste the code below and click Submit")
    
    auth_code = st.text_input("Authorization code:", key="auth_code_input", placeholder="Paste your authorization code here")
    
    if st.button("Submit Code", key="submit_auth_code"):
        if auth_code:
            with st.spinner("Authenticating..."):
                token = exchange_code_for_token(auth_code)
                if token:
                    st.session_state["access_token"] = token
                    profile = get_user_profile(token)
                    if profile:
                        name = profile.get("displayName") or profile.get("userPrincipalName", "User")
                        email = profile.get("mail") or profile.get("userPrincipalName", "")
                        st.session_state["user_info"] = {"name": name, "email": email}
                        st.success(f"✅ Welcome, {name}!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to fetch user profile after token exchange.")
                else:
                    st.error("❌ Token exchange failed. Please check your authorization code and try again.")
        else:
            st.warning("⚠️ Please enter an authorization code.")

def show_authentication_page():
    """Show authentication page with demo and production options"""
    st.subheader("🔐 Authentication Required")

    # Offer Demo and Production login options
    col1, col2 = st.columns(2)
    with col1:
        st.info("**Demo Mode**")
        handle_demo_login()
    
    with col2:
        st.info("**Production Mode**")
        handle_production_login()

def show_sidebar_navigation():
    """Show sidebar with user info and navigation"""
    user_info = st.session_state.get("user_info", {})
    
    with st.sidebar:
        st.success(f"👋 Welcome, {user_info.get('name', 'User')}!")
        
        if st.button("🚪 Logout"):
            logout()
            st.rerun()
        
        st.divider()
        
        # Navigation menu
        page = st.selectbox(
            "📋 Navigation",
            [VIEW_BOOKS_PAGE, ADD_BOOK_PAGE, MANAGE_BOOKS_PAGE, ABOUT_PAGE]
        )
    
    return page

def main():
    st.title("📚 Book Management Application")
    st.markdown("*Powered by Azure Services: VM, Cosmos DB, Key Vault, and Azure AD*")
    
    # Authentication check
    if not check_authentication():
        show_authentication_page()
        return
    
    # User is authenticated - show the main application
    page = show_sidebar_navigation()
    
    # Main content area
    if page == VIEW_BOOKS_PAGE:
        show_books_page()
    elif page == ADD_BOOK_PAGE:
        show_add_book_page()
    elif page == MANAGE_BOOKS_PAGE:
        show_manage_books_page()
    elif page == ABOUT_PAGE:
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

def handle_book_edit(book, book_id):
    """Handle book editing functionality"""
    with st.form("edit_book_form"):
        title = st.text_input("Title", value=book.get("title", ""))
        author = st.text_input("Author", value=book.get("author", ""))
        description = st.text_area("Description", value=book.get("description", ""))
        published_date = st.date_input("Published Date")
        
        if st.form_submit_button("💾 Update Book"):
            if title and author:
                try:
                    updated_book_data = {
                        "title": title,
                        "author": author,
                        "description": description,
                        "published_date": str(published_date)
                    }
                    
                    token = st.session_state.get("access_token")
                    success = update_book(BACKEND_URL, token, book_id, updated_book_data)
                    
                    if success:
                        st.success("✅ Book updated successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to update book")
                        
                except Exception as e:
                    st.error(f"❌ Error updating book: {e}")
                    logger.error(f"Error in update_book: {e}")
            else:
                st.warning("⚠️ Please fill in all required fields (Title and Author)")

def handle_book_delete(book_id):
    """Handle book deletion functionality"""
    st.warning("⚠️ This action cannot be undone!")
    if st.button("🗑️ Delete Book", type="secondary", key=f"delete_{book_id}"):
        try:
            token = st.session_state.get("access_token")
            success = delete_book(BACKEND_URL, token, book_id)
            
            if success:
                st.success("✅ Book deleted successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to delete book")
                
        except Exception as e:
            st.error(f"❌ Error deleting book: {e}")
            logger.error(f"Error in delete_book: {e}")

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
                        handle_book_edit(book, book_id)
                    
                    with tab2:
                        handle_book_delete(book_id)
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
