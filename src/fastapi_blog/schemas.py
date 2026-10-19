from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, EmailStr

# User
class User(BaseModel):
    username: str = Field(min_length=3)
    email: EmailStr = Field(min_length=5)

class UserCreate(User):
    pass

class UserUpdate(BaseModel):
    username: str = Field(default=None, min_length=3)
    email: EmailStr = Field(default=None, min_length=5)
    image_file: str | None = Field(default=None, min_length=5)

class UserResponse(User):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_file: str | None
    image_path: str


# Person
class Person(BaseModel):
    firstname: str = Field(min_length=1)
    lastname: str = Field(min_length=1)
    age: int
    phone: str = Field(max_length=10)
    reportTo: int | None 

class PersonCreate(Person):
    pass 

class PersonUpdate(BaseModel):
    firstname: str = Field(default=None, min_length=1)
    lastname: str = Field(default=None, min_length=1)
    age: int = Field(default=None)
    phone: str = Field(default=None)
    reportTo: int | None = Field(default=None)

class PersonResponse(Person):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner: UserResponse
    date_posted: datetime