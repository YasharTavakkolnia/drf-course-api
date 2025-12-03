from __future__ import annotations

from threading import Lock
from typing import Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, validator


app = FastAPI(title="Library API")


class BookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    author: str = Field(..., min_length=1, max_length=120)
    year: int = Field(..., ge=0)
    genre: Optional[str] = Field(None, min_length=1, max_length=60)


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    author: Optional[str] = Field(None, min_length=1, max_length=120)
    year: Optional[int] = Field(None, ge=0)
    genre: Optional[str] = Field(None, min_length=1, max_length=60)

    @validator("title", "author", "genre")
    def strip_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return value.strip()

    def ensure_payload(self) -> None:
        if not any(
            [
                self.title is not None,
                self.author is not None,
                self.year is not None,
                self.genre is not None,
            ]
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one field must be provided for update.",
            )


class Book(BookBase):
    id: str


class BookListCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    book_ids: List[str] = []


class BookList(BookListCreate):
    id: str


book_store: Dict[str, Book] = {}
book_list_store: Dict[str, BookList] = {}
store_lock = Lock()


@app.post("/books", response_model=Book, status_code=status.HTTP_201_CREATED)
def create_book(book: BookCreate) -> Book:
    with store_lock:
        book_id = str(uuid4())
        new_book = Book(id=book_id, **book.dict())
        book_store[book_id] = new_book
    return new_book


@app.get("/books", response_model=List[Book])
def list_books(
    query: Optional[str] = None,
    sort_by: str = "title",
    sort_direction: str = "asc",
) -> List[Book]:
    books = list(book_store.values())
    if query:
        lowered = query.lower()
        books = [
            book
            for book in books
            if lowered in book.title.lower()
            or lowered in book.author.lower()
            or (book.genre and lowered in book.genre.lower())
        ]

    valid_sort_fields = {"title", "author", "year", "genre"}
    if sort_by not in valid_sort_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"sort_by must be one of: {', '.join(sorted(valid_sort_fields))}",
        )

    reverse = sort_direction.lower() == "desc"
    books.sort(key=lambda book: getattr(book, sort_by) or "", reverse=reverse)
    return books


@app.get("/books/{book_id}", response_model=Book)
def get_book(book_id: str) -> Book:
    book = book_store.get(book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found.")
    return book


@app.put("/books/{book_id}", response_model=Book)
def update_book(book_id: str, updates: BookUpdate) -> Book:
    updates.ensure_payload()
    with store_lock:
        stored_book = book_store.get(book_id)
        if not stored_book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Book not found."
            )

        updated_data = stored_book.dict()
        for field, value in updates.dict(exclude_unset=True).items():
            updated_data[field] = value

        updated_book = Book(**updated_data)
        book_store[book_id] = updated_book
    return updated_book


@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: str) -> None:
    with store_lock:
        if book_id not in book_store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Book not found."
            )
        del book_store[book_id]

        for book_list in book_list_store.values():
            book_list.book_ids = [bid for bid in book_list.book_ids if bid != book_id]


@app.get("/books/search", response_model=List[Book])
def search_books(query: str) -> List[Book]:
    return list_books(query=query)


@app.post("/booklists", response_model=BookList, status_code=status.HTTP_201_CREATED)
def create_book_list(book_list: BookListCreate) -> BookList:
    with store_lock:
        missing = [book_id for book_id in book_list.book_ids if book_id not in book_store]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown book ids: {', '.join(missing)}",
            )

        list_id = str(uuid4())
        new_list = BookList(id=list_id, **book_list.dict())
        book_list_store[list_id] = new_list
    return new_list


@app.get("/booklists", response_model=List[BookList])
def list_book_lists() -> List[BookList]:
    return list(book_list_store.values())


@app.get("/booklists/{book_list_id}", response_model=BookList)
def get_book_list(book_list_id: str) -> BookList:
    book_list = book_list_store.get(book_list_id)
    if not book_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book list not found.",
        )
    return book_list
