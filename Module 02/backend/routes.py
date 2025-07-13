from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from .models import Book
from .database import get_table_client
from .auth import verify_token
import logging

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

book_router = APIRouter()

# Constants
BOOK_NOT_FOUND_MSG = "Book not found"

class ResponseModel(BaseModel):
    message: str
    success: bool

class ErrorResponseModel(BaseModel):
    detail: str
    success: bool = False

@book_router.post("/books", response_model=ResponseModel)
def create_book(book: Book, token: str = Depends(verify_token)):
    try:
        table_client = get_table_client()
        entity = book.to_table_entity()
        result = table_client.create_entity(entity)
        
        if result.get("success"):
            logger.info(f"Book created: {book.RowKey}")
            return {"message": "Book created successfully!", "success": True}
        else:
            raise HTTPException(status_code=500, detail="Failed to create book in database")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating book: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create book: {str(e)}")

@book_router.get("/books")
def get_books(token: str = Depends(verify_token)):
    try:
        table_client = get_table_client()
        entities = table_client.list_entities(partition_key="books")
        
        # Convert entities to list and ensure they're serializable
        books_list = []
        for entity in entities:
            # Convert TableEntity to dict
            book_dict = dict(entity)
            books_list.append(book_dict)
        
        logger.info(f"Fetched {len(books_list)} books")
        return books_list
        
    except Exception as e:
        logger.error(f"Error fetching books: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch books: {str(e)}")

@book_router.get("/books/{book_id}")
def get_book(book_id: str, token: str = Depends(verify_token)):
    try:
        table_client = get_table_client()
        entity = table_client.get_entity("books", book_id)
        
        if entity is None:
            raise HTTPException(status_code=404, detail=BOOK_NOT_FOUND_MSG)
        
        # Convert TableEntity to dict
        book_dict = dict(entity)
        logger.info(f"Fetched book: {book_id}")
        return book_dict
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching book {book_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch book: {str(e)}")

@book_router.put("/books/{book_id}", response_model=ResponseModel)
def update_book(book_id: str, book: Book, token: str = Depends(verify_token)):
    try:
        table_client = get_table_client()
        
        # First check if the book exists
        existing_entity = table_client.get_entity("books", book_id)
        if existing_entity is None:
            raise HTTPException(status_code=404, detail=BOOK_NOT_FOUND_MSG)
        
        # Ensure the RowKey matches the book_id
        book.RowKey = book_id
        entity = book.to_table_entity()
        
        result = table_client.update_entity(entity, mode="merge")
        
        if result.get("success"):
            logger.info(f"Book updated: {book_id}")
            return {"message": "Book updated successfully!", "success": True}
        else:
            raise HTTPException(status_code=500, detail="Failed to update book in database")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating book {book_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update book: {str(e)}")

@book_router.delete("/books/{book_id}", response_model=ResponseModel)
def delete_book(book_id: str, token: str = Depends(verify_token)):
    try:
        table_client = get_table_client()
        
        # First check if the book exists
        existing_entity = table_client.get_entity("books", book_id)
        if existing_entity is None:
            raise HTTPException(status_code=404, detail=BOOK_NOT_FOUND_MSG)
        
        result = table_client.delete_entity("books", book_id)
        
        if result.get("success"):
            logger.info(f"Book deleted: {book_id}")
            return {"message": "Book deleted successfully!", "success": True}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete book from database")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting book {book_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete book: {str(e)}")
