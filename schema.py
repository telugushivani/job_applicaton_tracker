from pydantic import BaseModel, model_validator
from datetime import date

class JobApplication(BaseModel):
    company:str
    job_role: str
    location: str
    employment_type:str
    source:str
    salary_min:int
    salary_max:int
    application_date: date
    status: str
    job_url: str
    @model_validator(mode="after")
    def validate_salary(self):
        if self.salary_min > self.salary_max:
            raise ValueError(
                "Minimum salary cannot exceed maximum salary"
            )
        return self 

class JobApplicationUpdate(BaseModel):  
    company:str | None=None
    job_role: str | None=None
    location: str | None=None
    employment_type:str | None=None
    source:str | None=None
    salary_min:int | None=None
    salary_max:int | None=None
    application_date: date | None=None
    status: str | None=None
    job_url: str | None=None  

       



class UserRegister(BaseModel):
    name: str
    email: str
    password: str



class UserLogin(BaseModel):
    email: str
    password: str

