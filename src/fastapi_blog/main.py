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
from .schemas import PersonResponse, PersonCreate, PersonUpdate, UserResponse, UserCreate, UserUpdate

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount("/media", StaticFiles(directory="src/fastapi_blog/media"), name="media") 

templates = Jinja2Templates(directory="templates")

@app.get("/")
def home(request: Request, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(model.Person))
    persons = result.scalars().all()
    return templates.TemplateResponse(
        request, 
        "home.html", 
        {"persons": persons}
    )

@app.get("/api/persons", response_model=list[PersonResponse])
def get_persons(db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(model.Person))
    return result.scalars().all()

@app.get("/api/persons/{person_id}", response_model=PersonResponse)
def persons_page(request: Request, person_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(model.Person).where(model.Person.id == person_id)
    )
    person = result.scalars().first()

    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Person not found"
        )
    return templates.TemplateResponse(
            request, 
            "person.html", 
            {"person": person}
    )

@app.delete("/api/persons/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_persons(person_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(model.Person).where(model.Person.id == person_id)
    )
    person = result.scalars().first()

    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Person not found"
        )

    db.delete(person)
    db.commit()


@app.put("/api/persons/{person_id}", response_model=PersonResponse)
def update_person(person_id: int, person_data:PersonCreate, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(model.Person).where(model.Person.id == person_id)
    )
    person = result.scalars().first()

    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Person not found"
        )

    if person_data.reportTo != person.reportTo:
        result = db.execute(
            select(model.User).where(model.User.id == person_data.reportTo)
        )
        user = result.scalars().first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Person not found"
            )

    person.firstname = person_data.firstname
    person.lastname = person_data.lastname
    person.age = person_data.age
    person.phone = person_data.phone
    person.reportTo = person_data.reportTo

    db.commit()
    db.refresh(person)
    return person

@app.patch("/api/persons/{person_id}", response_model=PersonResponse)
def update_person_partial(person_id: int, person_data: PersonUpdate, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(model.Person).where(model.Person.id == person_id)
    )
    person = result.scalars().first()

    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Person not found"
        )

    update_data = person_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(person, field, value)

    db.commit()
    db.refresh(person)
    return person


@app.get("/api/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(model.User).where(model.User.id == user_id)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@app.get("/api/users/{user_id}/persons", response_model=list[PersonResponse])
def get_user_persons(user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(model.User).where(model.User.id == user_id)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    result = db.execute(
        select(model.Person).where(model.Person.reportTo == user_id)
    )
    return result.scalars().all()

@app.post("/api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(model.User).where(model.User.email == user.email),
    )
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )
    new_user = model.User(
        username=user.username,
        email=user.email
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.patch("/api/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_data: UserUpdate, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(model.User).where(model.User.id == user_id)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Person not found"
        )

    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user

@app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_persons(user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(model.User).where(model.User.id == user_id)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Person not found"
        )

    db.delete(user)
    db.commit()

@app.post("/api/persons", response_model=PersonResponse, status_code=status.HTTP_201_CREATED)
def create_person(person: PersonCreate, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(model.User).where(model.User.id == person.reportTo)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User (reportTo) not found"
        )

    new_person = model.Person(
        firstname=person.firstname,
        lastname=person.lastname,
        age=person.age,
        phone=person.phone,
        reportTo=person.reportTo
    )
    db.add(new_person)
    db.commit()
    db.refresh(new_person)
    return new_person

@app.exception_handler(StarletteHTTPException)
def general_exception_handler(request: Request, exception: StarletteHTTPException):
    message = exception.detail if exception.detail else "An error occurred"

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