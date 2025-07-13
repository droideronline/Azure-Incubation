import requests
import streamlit as st
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for error messages
AUTH_FAILED_MSG = "Authentication failed. Please login again."
UNKNOWN_ERROR_MSG = "Unknown error"
API_CONNECTION_ERROR_MSG = "Cannot connect to the API. Please check if the backend is running."
REQUEST_TIMEOUT_MSG = "Request timed out. Please try again."

def get_books(api_url, token):
    """
    Fetch all books from the API
    """
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{api_url}/books", headers=headers, timeout=10)
        
        if response.status_code == 200:
            books = response.json()
            logger.info(f"Successfully fetched {len(books)} books")
            return books
        elif response.status_code == 401:
            st.error(AUTH_FAILED_MSG)
            return []
        elif response.status_code == 403:
            st.error("Access denied. You don't have permission to view books.")
            return []
        else:
            error_msg = f"Failed to fetch books: {response.status_code}"
            try:
                error_detail = response.json().get('detail', UNKNOWN_ERROR_MSG)
                error_msg += f" - {error_detail}"
            except requests.exceptions.JSONDecodeError:
                error_msg += f" - {response.text}"
            logger.error(error_msg)
            st.error(error_msg)
            return []
            
    except requests.exceptions.Timeout:
        error_msg = REQUEST_TIMEOUT_MSG
        logger.error(error_msg)
        st.error(error_msg)
        return []
    except requests.exceptions.ConnectionError:
        error_msg = API_CONNECTION_ERROR_MSG
        logger.error(error_msg)
        st.error(error_msg)
        return []
    except Exception as e:
        error_msg = f"Unexpected error fetching books: {e}"
        logger.error(error_msg)
        st.error(error_msg)
        return []

def add_book(api_url, token, book_data):
    """
    Add a new book via the API
    """
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(f"{api_url}/books", json=book_data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                logger.info("Successfully added book")
                return True
            else:
                st.error(f"Failed to add book: {result.get('message', UNKNOWN_ERROR_MSG)}")
                return False
        elif response.status_code == 401:
            st.error(AUTH_FAILED_MSG)
            return False
        elif response.status_code == 403:
            st.error("Access denied. You don't have permission to add books.")
            return False
        else:
            error_msg = f"Failed to add book: {response.status_code}"
            try:
                error_detail = response.json().get('detail', UNKNOWN_ERROR_MSG)
                error_msg += f" - {error_detail}"
            except requests.exceptions.JSONDecodeError:
                error_msg += f" - {response.text}"
            logger.error(error_msg)
            st.error(error_msg)
            return False
            
    except requests.exceptions.Timeout:
        error_msg = REQUEST_TIMEOUT_MSG
        logger.error(error_msg)
        st.error(error_msg)
        return False
    except requests.exceptions.ConnectionError:
        error_msg = API_CONNECTION_ERROR_MSG
        logger.error(error_msg)
        st.error(error_msg)
        return False
    except Exception as e:
        error_msg = f"Unexpected error adding book: {e}"
        logger.error(error_msg)
        st.error(error_msg)
        return False

def update_book(api_url, token, book_id, book_data):
    """
    Update an existing book via the API
    """
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.put(f"{api_url}/books/{book_id}", json=book_data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                logger.info(f"Successfully updated book: {book_id}")
                return True
            else:
                st.error(f"Failed to update book: {result.get('message', UNKNOWN_ERROR_MSG)}")
                return False
        elif response.status_code == 401:
            st.error(AUTH_FAILED_MSG)
            return False
        elif response.status_code == 403:
            st.error("Access denied. You don't have permission to update books.")
            return False
        elif response.status_code == 404:
            st.error("Book not found.")
            return False
        else:
            error_msg = f"Failed to update book: {response.status_code}"
            try:
                error_detail = response.json().get('detail', UNKNOWN_ERROR_MSG)
                error_msg += f" - {error_detail}"
            except requests.exceptions.JSONDecodeError:
                error_msg += f" - {response.text}"
            logger.error(error_msg)
            st.error(error_msg)
            return False
            
    except requests.exceptions.Timeout:
        error_msg = REQUEST_TIMEOUT_MSG
        logger.error(error_msg)
        st.error(error_msg)
        return False
    except requests.exceptions.ConnectionError:
        error_msg = API_CONNECTION_ERROR_MSG
        logger.error(error_msg)
        st.error(error_msg)
        return False
    except Exception as e:
        error_msg = f"Unexpected error updating book: {e}"
        logger.error(error_msg)
        st.error(error_msg)
        return False

def delete_book(api_url, token, book_id):
    """
    Delete a book via the API
    """
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.delete(f"{api_url}/books/{book_id}", headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                logger.info(f"Successfully deleted book: {book_id}")
                return True
            else:
                st.error(f"Failed to delete book: {result.get('message', UNKNOWN_ERROR_MSG)}")
                return False
        elif response.status_code == 401:
            st.error(AUTH_FAILED_MSG)
            return False
        elif response.status_code == 403:
            st.error("Access denied. You don't have permission to delete books.")
            return False
        elif response.status_code == 404:
            st.error("Book not found.")
            return False
        else:
            error_msg = f"Failed to delete book: {response.status_code}"
            try:
                error_detail = response.json().get('detail', UNKNOWN_ERROR_MSG)
                error_msg += f" - {error_detail}"
            except requests.exceptions.JSONDecodeError:
                error_msg += f" - {response.text}"
            logger.error(error_msg)
            st.error(error_msg)
            return False
            
    except requests.exceptions.Timeout:
        error_msg = REQUEST_TIMEOUT_MSG
        logger.error(error_msg)
        st.error(error_msg)
        return False
    except requests.exceptions.ConnectionError:
        error_msg = API_CONNECTION_ERROR_MSG
        logger.error(error_msg)
        st.error(error_msg)
        return False
    except Exception as e:
        error_msg = f"Unexpected error deleting book: {e}"
        logger.error(error_msg)
        st.error(error_msg)
        return False

def check_api_health(api_url):
    """
    Check if the API is healthy and reachable
    """
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"API health check failed: {e}")
        return False
