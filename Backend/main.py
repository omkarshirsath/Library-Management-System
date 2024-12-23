from fastapi import FastAPI, Depends, HTTPException, Form
from fastapi.responses import JSONResponse
from mysql.connector import connect, MySQLConnection
from mysql.connector.errors import Error
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from datetime import date

app = FastAPI()

# CORS configuration
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:8000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Omkar@321",
    "database": "admin_db"
}

# Dependency to manage database connection
def get_db() -> MySQLConnection:
    try:
        db = connect(**DB_CONFIG)
        yield db  # Provide the connection for use
    except Error as e:
        raise HTTPException(status_code=500, detail="Database connection failed")
    finally:
        db.close()  # Close the connection when done

# Login request model
class LoginRequest(BaseModel):
    username: str
    password: str

# Book model
class Book(BaseModel):
    BookName: str
    Author: str
    Publisher: str
    Category: str
    ISBN: str
    Language: str
    Price: float
    TotalCopies: int
    AvailableCopies: int
    BookAddedDate: str
    ShelfLocation: str
    PublishedYear: int
    Description: str
    CoverImagePath: str
    Status: str

# Response model for books (inherit from Book)
class BookResponse(Book):
    BookID: int

    class Config:
        orm_mode = True

# Route: Login
@app.post("/login", tags=["Authentication"])
async def login(username: str = Form(...), password: str = Form(...), db: MySQLConnection = Depends(get_db)):
    """
    Login endpoint to authenticate a user.
    - **username**: Username of the admin.
    - **password**: Password of the admin.
    """
    cursor = db.cursor(dictionary=True)
    try:
        # Query to verify user credentials
        query = "SELECT * FROM admin_users WHERE username = %s AND password = %s"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")

        return JSONResponse(content={"message": "Login successful", "username": user["username"]}, status_code=200)
    finally:
        cursor.close()

@app.post("/insert-books", tags=["Books"])
async def insert_book(book: Book, db: MySQLConnection = Depends(get_db)):
    """
    Endpoint to insert a book into the database.
    - **book**: The book information to be inserted.
    """
    cursor = db.cursor()
    try:
        # SQL query to insert the book, including all columns (no default values)
        query = """
            INSERT INTO Books 
            (BookName, Author, Publisher, Category, ISBN, Language, Price, TotalCopies, 
            AvailableCopies, BookAddedDate, ShelfLocation, PublishedYear, Description, 
            CoverImagePath, Status)
            VALUES 
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        
        # Values to insert, coming from the request body (book)
        values = (
            book.BookName, book.Author, book.Publisher, book.Category, book.ISBN, 
            book.Language, book.Price, book.TotalCopies, book.AvailableCopies,
            book.BookAddedDate, book.ShelfLocation, book.PublishedYear, book.Description, 
            book.CoverImagePath, book.Status
        )

        # Execute the query
        cursor.execute(query, values)
        db.commit()  # Commit the transaction

        return JSONResponse(content={"message": "Book inserted successfully"}, status_code=201)
    
    except Error as e:
        db.rollback()  # Rollback in case of an error
        raise HTTPException(status_code=500, detail=f"Error inserting book: {str(e)}")
    
    finally:
        cursor.close()  # Close the cursor


@app.get("/get-books", response_model=List[BookResponse], tags=["Books"])
async def get_books(db: MySQLConnection = Depends(get_db)):
    """
    Retrieve all books from the database.
    """
    cursor = db.cursor(dictionary=True)
    try:
        # Query to fetch all books from the Books table
        query = "SELECT * FROM Books"
        cursor.execute(query)
        books = cursor.fetchall()

        # Convert date fields to strings
        for book in books:
            if isinstance(book["BookAddedDate"], date):
                book["BookAddedDate"] = book["BookAddedDate"].isoformat()

        return [BookResponse(**book) for book in books]
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve books: {str(e)}")
    finally:
        cursor.close()
# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
