from typing import Annotated

from fastapi import FastAPI, Request, HTTPException, status, Depends

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import model
from ..database import Base, engine, get_db
from ..schemas import PersonResponse, PersonCreate, PersonUpdate, UserResponse, UserCreate, UserUpdate