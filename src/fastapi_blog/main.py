from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Annotated
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import model
from .database import Base, engine, get_db
from .schemas import PersonResponse, PersonCreate, UserResponse, UserCreate

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount("media", StaticFiles(directory="media"), name="media")

templates = Jinja2Templates(directory="templates")

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request, 
        "home.html", 
        {"persons": persons}
    )

@app.get("/hypertext", include_in_schema=False)
def get_html(): 
    return f"<p>{persons[1]['lastname']}</p>"

@app.get("/persons", response_model=list[PersonResponse])
def get_persons():
    return persons

@app.get("/api/persons/{person_id}", response_model=PersonResponse)
def persons_page(request: Request, person_id: str):
    for person in persons:
        if person.get("id") == person_id:
            title = person["firstname"][:50]
            return templates.TemplateResponse(
                request,
                "person.html",
                {"person": person, "title": title},
            )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, 
        detail="Person not found"
    )

@app.post("/api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Annotated[Session, Depends(get_db)]):
    pass


@app.post("/api/persons", response_model=PersonResponse, status_code=status.HTTP_201_CREATED)
def create_person(person: PersonCreate):
    new_id = max(p["id"] for p in persons) + 1 if persons else 1

    new_person = {
        "id": new_id,
        "firstname": person.firstname,
        "lastname": person.lastname,
        "age": person.age,
        "phone": person.phone,
        "date_posted": "Mon 12 Oct 2026"
    }
    persons.append(new_person)
    return new_person

@app.exception_handler(StarletteHTTPException)
def general_exception_handler(request: Request, exception: StarletteHTTPException):
    message = (
        exception.detail
        if exception.detail
        else "An error occured"
    )

    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exception.status_code,
            content={"detail": message}
        )
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exception.status_code,
            "title": exception.status_code,
            "message": message,
        }
    )

@app.exception_handler(RequestValidationError)
def validator_exception_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": exception.errors()}
        )
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message": "Invalid request",
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT
    )