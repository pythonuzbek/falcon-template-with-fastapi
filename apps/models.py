import typing as t
from datetime import datetime

from sqlalchemy import Boolean, Numeric, SmallInteger, text, DateTime, func, Text
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import relationship

class_registry: t.Dict = {}


@as_declarative(class_registry=class_registry)
class Base:
    id: t.Any
    __name__: str

    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


class Users(Base):
    id: int = Column(Integer, primary_key=True)
    name: str = Column(String(100))
    email: str = Column(String(50), unique=True)
    is_active: str = Column(Boolean, default=False)
    password: str = Column(String(255))
    products = relationship('Product', back_populates='author')
    image = Column(String(255))
    card = relationship('Card', back_populates='user')
    like = relationship('Like', back_populates='user')
    updated_at: datetime = Column(DateTime, onupdate=datetime.now)
    created_at: datetime = Column(DateTime, server_default=func.now())
    review = relationship('Review', back_populates='user')


class Category(Base):
    id: int = Column(Integer, primary_key=True)
    name: str = Column(String(50), nullable=False)
    products = relationship('Product', back_populates='category')


class Product(Base):
    id: int = Column(Integer, primary_key=True)
    name: str = Column(String(50), nullable=False)
    price: float = Column(Numeric(9, 2), nullable=False)
    discount: int = Column(SmallInteger, server_default=text('0'))
    description: str = Column(String(512))
    specifications: dict = Column(JSONB, server_default=text("'{}'::jsonb"))

    author_id: int = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    author = relationship('Users', back_populates='products')

    category_id: int = Column(Integer, ForeignKey('category.id', ondelete='CASCADE'), nullable=False)
    category = relationship('Category', back_populates='products')

    images = relationship('ProductImage', back_populates='product')
    card = relationship('Card', back_populates='product')
    like = relationship('Like', back_populates='product')
    review = relationship('Review', back_populates='product')

    @property
    def discount_price(self):
        return self.price - round(self.price * self.discount / 100, 2)


class ProductImage(Base):
    id: int = Column(Integer, primary_key=True)
    image: str = Column(String(255))
    product_id: int = Column(Integer, ForeignKey('product.id', ondelete='CASCADE'), nullable=False)
    product = relationship('Product', back_populates='images')


class Card(Base):
    id: int = Column(Integer, primary_key=True)
    user_id: int = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    user = relationship('Users', back_populates='card')
    product_id: int = Column(Integer, ForeignKey('product.id', ondelete='CASCADE'), nullable=False)
    product = relationship('Product', back_populates='card')
    total = Column(Integer, server_default=text('0'))


class Like(Base):
    id: int = Column(Integer, primary_key=True)
    user_id: int = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    user = relationship('Users', back_populates='like')
    product_id: int = Column(Integer, ForeignKey('product.id', ondelete='CASCADE'), nullable=False)
    product = relationship('Product', back_populates='like')
    total = Column(Integer, server_default=text('0'))


class Review(Base):
    id: int = Column(Integer, primary_key=True)
    title: str = Column(String(255))
    text: str = Column(Text)
    star: int = Column(Integer)
    created_at: datetime = Column(DateTime, server_default=func.now())
    user_id: int = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    user = relationship('Users', back_populates='review')
    product_id: int = Column(Integer, ForeignKey('product.id', ondelete='CASCADE'), nullable=False)
    product = relationship('Product', back_populates='review')

#
# class Company(Base):
#     id: int = Column(Integer, primary_key=True)
#     name: str = Column(String(50))
#     employees: Mapped[list['Employee']] = relationship(
#         'Employee',
#         secondary=company_employee_table,
#         back_populates="companies",
#         cascade="all, delete"
#     )


#
# class Position(Base):
#     id: int = Column(Integer, primary_key=True)
#     name: str = Column(String(50))
#     employees = relationship('Employee', uselist=False, back_populates='position')
#

# class Employee(Base):
#     id: int = Column(Integer, primary_key=True)
#     name: str = Column(String(50))
#     email: str = Column(String(50))
#     address: str = Column(String(255))
#     phone: str = Column(String(15))
#     media: str = Column(String(255))
#
#     position_id: int = Column(Integer, ForeignKey('position.id'))
#     position = relationship('Position', back_populates='employees')
#     companies = relationship(
#         'Company',
#         secondary=company_employee_table,
#         back_populates="employees"
#     )
#
#     def __repr__(self):
#         return self.name
