from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from models import Book
from database import get_table_client
import logging

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

book_router = APIRouter()

class ResponseModel(BaseModel):
    message: str

@book_router.post("/books", response_model=ResponseModel)
def create_book(book: Book):
    try:
        table_client = get_table_client()
        entity = book.to_table_entity()
        result = table_client.create_entity(entity)
        logger.info(f"Book created: {book.RowKey}")
        return {"message": "Book created successfully!"}
    except Exception as e:
        logger.error(f"Error creating book: {e}")
        raise HTTPException(status_code=500, detail="Failed to create book")

@book_router.get("/books")
def get_books():
    try:
        table_client = get_table_client()
        entities = table_client.list_entities()
        logger.info("Fetched all books")
        return entities
    except Exception as e:
        logger.error(f"Error fetching books: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch books")

@book_router.get("/books/{book_id}")
def get_book(book_id: str):
    try:
        table_client = get_table_client()
        entity = table_client.get_entity("books", book_id)
        logger.info(f"Fetched book: {book_id}")
        return entity
    except Exception as e:
        logger.error(f"Error fetching book {book_id}: {e}")
        raise HTTPException(status_code=404, detail="Book not found")

@book_router.put("/books/{book_id}", response_model=ResponseModel)
def update_book(book_id: str, book: Book):
    try:
        table_client = get_table_client()
        # Ensure the RowKey matches the book_id
        book.RowKey = book_id
        entity = book.to_table_entity()
        table_client.update_entity(entity)
        logger.info(f"Book updated: {book_id}")
        return {"message": "Book updated successfully!"}
    except Exception as e:
        logger.error(f"Error updating book {book_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update book")

@book_router.delete("/books/{book_id}", response_model=ResponseModel)
def delete_book(book_id: str):
    try:
        table_client = get_table_client()
        table_client.delete_entity("books", book_id)
        logger.info(f"Book deleted: {book_id}")
        return {"message": "Book deleted successfully!"}
    except Exception as e:
        logger.error(f"Error deleting book {book_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete book")
