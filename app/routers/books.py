from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlmodel import Session, select
from app.models import Book
from app.database import get_session
from app.auth import get_current_user

router = APIRouter(prefix="/books", tags=["books"])

"""                            PUBLIC ROUTES                             """


@router.get("/")
def read_books(skip: int = 0, limit: int = 10, session: Session = Depends(get_session)):
    books = session.exec(select(Book).offset(skip).limit(limit)).all()
    return jsonable_encoder(books)


@router.get("/{book_id}")
def read_book(book_id: int, session: Session = Depends(get_session)):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return jsonable_encoder(book)


"""                            PROTECTED ROUTES                             """


@router.post("/")
def create_book(
    title: str,
    author: str,
    description: str,
    session: Session = Depends(get_session),
    current_user: str = Depends(get_current_user)
):
    new_book = Book(title=title, author=author, description=description)
    session.add(new_book)
    session.commit()
    session.refresh(new_book)
    return JSONResponse(
        status_code=201,
        content={
            "message": "Book added successfully",
            "book": jsonable_encoder(new_book)
        }
    )


@router.put("/{book_id}")
def update_book(
    book_id: int,
    title: str | None = None,
    author: str | None = None,
    description: str | None = None,
    session: Session = Depends(get_session),
    current_user: str = Depends(get_current_user)
):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Update only the provided fields
    update_data = {key: value for key, value in {
        "title": title,
        "author": author,
        "description": description
    }.items() if value is not None}

    for key, value in update_data.items():
        setattr(book, key, value)

    session.commit()
    session.refresh(book)

    return JSONResponse(
        status_code=200,
        content={
            "message": "Book updated successfully",
            "book": jsonable_encoder(book)
        }
    )


@router.delete("/{book_id}")
def delete_book(
    book_id: int,
    session: Session = Depends(get_session),
    current_user: str = Depends(get_current_user)
):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    session.delete(book)
    session.commit()
    return JSONResponse(status_code=200, content={"message": "Book deleted successfully"})
