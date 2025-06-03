import requests
import streamlit as st
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_books(api_url, token):
    """
    Fetch all books from the API
    """
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{api_url}/books", headers=headers)
        
        if response.status_code == 200:
            books = response.json()
            logger.info(f"Successfully fetched {len(books)} books")
            return books
        else:
            logger.error(f"Failed to fetch books: {response.status_code}")
            return []
            
    except Exception as e:
        logger.error(f"Error fetching books: {e}")
        st.error(f"Network error: {e}")
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
        
        response = requests.post(f"{api_url}/books", json=book_data, headers=headers)
        
        if response.status_code == 200:
            logger.info("Successfully added book")
            return True
        else:
            logger.error(f"Failed to add book: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error adding book: {e}")
        st.error(f"Network error: {e}")
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
        
        response = requests.put(f"{api_url}/books/{book_id}", json=book_data, headers=headers)
        
        if response.status_code == 200:
            logger.info(f"Successfully updated book: {book_id}")
            return True
        else:
            logger.error(f"Failed to update book: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error updating book: {e}")
        st.error(f"Network error: {e}")
        return False

def delete_book(api_url, token, book_id):
    """
    Delete a book via the API
    """
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.delete(f"{api_url}/books/{book_id}", headers=headers)
        
        if response.status_code == 200:
            logger.info(f"Successfully deleted book: {book_id}")
            return True
        else:
            logger.error(f"Failed to delete book: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error deleting book: {e}")
        st.error(f"Network error: {e}")
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
