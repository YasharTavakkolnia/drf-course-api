# FastAPI Library API

A lightweight FastAPI project that manages books and named book lists.

## Features
- Add, remove, update, search, and sort books
- Create and fetch book lists made up of existing books

## Running locally
Install the dependencies and start the development server:

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The API documentation is available at <http://127.0.0.1:8000/docs> after the server starts.

## Example requests
- **Create a book**
  ```bash
  curl -X POST http://127.0.0.1:8000/books \
    -H "Content-Type: application/json" \
    -d '{"title": "Dune", "author": "Frank Herbert", "year": 1965, "genre": "Science Fiction"}'
  ```

- **Search and sort books**
  ```bash
  curl "http://127.0.0.1:8000/books?query=dune&sort_by=year&sort_direction=desc"
  ```

- **Create a book list**
  ```bash
  curl -X POST http://127.0.0.1:8000/booklists \
    -H "Content-Type: application/json" \
    -d '{"name": "Favorites", "book_ids": ["<book-id>"]}'
  ```
