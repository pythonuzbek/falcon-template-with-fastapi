import re

from fastapi import Form, File, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from apps import models
from apps.hashing import Hasher


class EmployeeForm(BaseModel):
    name: str
    email: str
    address: str
    phone: str
    image: UploadFile

    @classmethod
    def as_form(
            cls,
            name: str = Form(...),
            email: str = Form(...),
            address: str = Form(...),
            phone: str = Form(...),
            image: UploadFile = File(...)
    ):
        return cls(name=name, email=email, address=address, phone=phone, image=image)


class RegisterForm(BaseModel):
    name: str
    email: str
    password: str
    confirm_password: str

    def is_valid(self, db: Session):
        errors = []
        if self.confirm_password != self.password:
            errors.append('Password did not match!')

        regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
        if not re.search(regex, self.email):
            errors.append('Must be a valid email address')
        self.confirm_password = None
        q = db.query(models.Users).filter(models.Users.email == self.email)
        exists = db.query(q.exists()).first()[0]

        if exists:
            errors.append('Must be a unique email address')

        self.password = Hasher.get_password_hash(self.password)
        return errors

    @classmethod
    def as_form(
            cls,
            name: str = Form(...),
            email: str = Form(...),
            password: str = Form(...),
            confirm_password: str = Form(...)
    ):
        return cls(name=name, email=email, password=password, confirm_password=confirm_password)


class LoginForm(BaseModel):
    email: str
    password: str

    def is_valid(self, db: Session):
        errors = []

        user: models.Users = db.query(models.Users).filter(models.Users.email == self.email).first()
        if not user:
            errors.append('User not found!')
        elif not Hasher.verify_password(self.password, user.password):
            errors.append('Password does not match!')

        return errors, user

    @classmethod
    def as_form(
            cls,
            email: str = Form(...),
            password: str = Form(...),
    ):
        return cls(email=email, password=password)


class ProductForm(BaseModel):
    name: str
    description: str
    price: float
    category_id: int
    images: list[UploadFile]

    @classmethod
    def as_form(
            cls,
            name: str = Form(...),
            description: str = Form(...),
            price: str = Form(...),
            category_id: int = Form(...),
            images: list[UploadFile] = File(...)
    ):
        return cls(name=name, description=description, price=price, category_id=category_id, images=images)


class EditForm(BaseModel):
    name: str
    email: str
    image: UploadFile

    @classmethod
    def as_form(
            cls,
            name: str = Form(...),
            email: str = Form(...),
            image: UploadFile = File(...),

    ):
        return cls(name=name, email=email,
                   image=image)


class ForgotPassword(BaseModel):
    password: str
    confirm_password: str

    def is_valid(self, db: Session):
        errors = []
        if self.confirm_password != self.password:
            errors.append('Password did not match!')
        self.confirm_password = None
        self.password = Hasher.get_password_hash(self.password)
        return errors

    @classmethod
    def as_form(
            cls,
            password: str = Form(...),
            confirm_password: str = Form(...)
    ):
        return cls(password=password, confirm_password=confirm_password)


class ReviewForm(BaseModel):
    title: str
    text: str

    @classmethod
    def as_form(cls,
                title: str = Form(...),
                text: str = Form(...)):
        return cls(title=title, text=text)


class StarForm(BaseModel):
    star: int

    @classmethod
    def as_form(cls,
                star: int = Form(...)):
        return cls(star=star)
