from pydantic import BaseModel, Field, ConfigDict

class Person(BaseModel):
    firstname: str = Field(min_length=1)
    lastname: str = Field(min_length=1)
    age: int
    phone: str = Field(max_length=10)

class PersonCreate(Person):
    pass

class PersonResponse(Person):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date_posted: str