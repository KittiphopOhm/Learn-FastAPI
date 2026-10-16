from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, EmailStr

# User
class User(BaseModel):
    username: str = Field(min_length=3)
    email: EmailStr = Field(min_length=5)

class UserCreate(User):
    pass

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
    reportTo: str | None

class PersonCreate(Person):
    user_id: int

class PersonResponse(Person):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner: UserResponse
    date_posted: datetime