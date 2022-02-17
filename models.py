from pydantic import BaseModel, root_validator
from datetime import date


class Person(BaseModel):
    name: str
    dob: date

    @property
    def pid(self):
        return self.name.lower().replace(" ", "")+self.dob.isoformat().replace("-", "")


class Birthday(BaseModel):
    day: date
    age: int

    @staticmethod
    def increment_one_year(self) -> "Birthday":
        bday = self.day
        return Birthday(day=bday.replace(year=bday.year + 1), age=self.age + 1)


class EventResponse(BaseModel):
    id: str
    start: date
    summary: str
    description: str
    extended_properties: dict[str, dict[str, str]]

    @root_validator(pre=True)
    def extract_properties(cls, values):
        values["start"] = values["start"]["date"]
        values["extended_properties"] = values["extendedProperties"]
        return values
