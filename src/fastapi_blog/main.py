from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import model
from .database import Base, engine, get_db
from .schemas import PersonResponse, PersonCreate, PersonUpdate, UserResponse, UserCreate, UserUpdate

@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

app.mount("/media", StaticFiles(directory="src/fastapi_blog/media"), name="media") 

templates = Jinja2Templates(directory="templates")

@app.get("/")
async def home(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(model.Person).options(selectinload(model.Person.owner))
    )
    persons = result.scalars().all()
    return templates.TemplateResponse(
        request, 
        "home.html", 
        {"persons": persons}
    )


@app.get("/api/persons/{person_id}/view")
async def persons_page(request: Request, person_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(model.Person)
        .options(selectinload(model.Person.owner))
        .where(model.Person.id == person_id)
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

@app.get("/api/persons", response_model=list[PersonResponse])
async def get_persons(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(model.Person).options(selectinload(model.Person.owner))
    )
    return result.scalars().all()


@app.get("/api/persons/{person_id}", response_model=PersonResponse)
async def get_person_by_id(person_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(model.Person)
        .options(selectinload(model.Person.owner))
        .where(model.Person.id == person_id)
    )
    person = result.scalars().first()

    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Person not found"
        )
    return person


@app.post("/api/persons", response_model=PersonResponse, status_code=status.HTTP_201_CREATED)
async def create_person(person: PersonCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
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
    await db.commit()
    await db.refresh(new_person)
    
    result = await db.execute(
        select(model.Person)
        .options(selectinload(model.Person.owner))
        .where(model.Person.id == new_person.id)
    )
    return result.scalars().first()


@app.put("/api/persons/{person_id}", response_model=PersonResponse)
async def update_person(person_id: int, person_data: PersonCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(model.Person).where(model.Person.id == person_id)
    )
    person = result.scalars().first()

    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Person not found"
        )

    if person_data.reportTo != person.reportTo:
        user_result = await db.execute(
            select(model.User).where(model.User.id == person_data.reportTo)
        )
        user = user_result.scalars().first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Target User (reportTo) not found"
            )

    person.firstname = person_data.firstname
    person.lastname = person_data.lastname
    person.age = person_data.age
    person.phone = person_data.phone
    person.reportTo = person_data.reportTo

    await db.commit()
    await db.refresh(person)
    
    result = await db.execute(
        select(model.Person)
        .options(selectinload(model.Person.owner))
        .where(model.Person.id == person.id)
    )
    return result.scalars().first()


@app.patch("/api/persons/{person_id}", response_model=PersonResponse)
async def update_person_partial(person_id: int, person_data: PersonUpdate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
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

    await db.commit()
    await db.refresh(person)
    
    result = await db.execute(
        select(model.Person)
        .options(selectinload(model.Person.owner))
        .where(model.Person.id == person.id)
    )
    return result.scalars().first()


@app.delete("/api/persons/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person(person_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(model.Person).where(model.Person.id == person_id)
    )
    person = result.scalars().first()

    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Person not found"
        )

    await db.delete(person)
    await db.commit()


# --- USER API ENDPOINTS ---
@app.post("/api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
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
    await db.commit()
    await db.refresh(new_user)
    return new_user


@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
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
async def get_user_persons(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(model.User).where(model.User.id == user_id)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    result = await db.execute(
        select(model.Person)
        .options(selectinload(model.Person.owner))
        .where(model.Person.reportTo == user_id)
    )
    return result.scalars().all()


@app.patch("/api/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_data: UserUpdate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(model.User).where(model.User.id == user_id)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found"
        )

    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return user


@app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(model.User).where(model.User.id == user_id)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found"
        )

    await db.delete(user)
    await db.commit()


# --- EXCEPTION HANDLERS ---

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