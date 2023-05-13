import os
import shutil
from math import ceil, floor
from typing import Optional

from fastapi import APIRouter, Request, Depends, Form
from sqlalchemy import update, select
from sqlalchemy.orm import Session
from starlette.background import BackgroundTasks
from starlette.responses import RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER

from apps import models
from apps.forms import ProductForm, EditForm, ReviewForm, StarForm
from apps.models import Users
from config import manager
from config import templates
from database import get_db

product_api = APIRouter()


@product_api.get('/', name='product_list')
async def public_page(request: Request, db: Session = Depends(get_db),offset: int = 0, limit: int = 6):
    products = db.query(models.Product).order_by(-models.Product.id).limit(limit).offset(offset)
    image = db.query(models.ProductImage).all()
    users = db.query(models.Users).all()
    user = db.query(models.Users).filter(models.Users.id == request.state.user.id).first()
    count = db.query(models.Product).count()
    # for i in products:
    #     print(i.product.images)
    counter = 0
    for _ in products:
        counter += 1
    # res.append(db.query(models.Card).filter(request.state.user.id == models.Card.id))
    # res.append(card.total)
    # print(res)
    result = db.execute(select(models.Card).where(models.Card.user_id == request.state.user.id)).fetchall()
    print(type(result))
    c = 0
    for i in result:
        c += i[0].total
    print(c)
    context = {
        'request': request,
        'products': products,
        'users': users,
        'count2': c,
        'limit': limit,
        'offset': offset,
        'count': ceil(count / limit),
        'counter': count,
        'user': user,
        'images': image
    }
    return templates.TemplateResponse('products/product-list.html', context)


@product_api.get('/detail/{pk}', name='product_detail')
async def private_page(request: Request, pk: int, db: Session = Depends(get_db)):
    user = db.query(models.Users).filter(models.Users.id == request.state.user.id).first()
    product = db.query(models.Product).where(models.Product.id == pk).first()
    context = {
        'request': request,
        'user': user,
        'product': product
    }
    return templates.TemplateResponse('products/product-details.html', context)


@product_api.get('/add', name='product_add')
async def private_page(request: Request, db: Session = Depends(get_db), current_user=Depends(manager)):
    user = db.query(models.Users).filter(models.Users.id == request.state.user.id).first()
    context = {
        'request': request,
        'user': user
    }
    return templates.TemplateResponse('products/product-add.html', context)


def save_image(images, product_id, db: Session):
    if isinstance(images, list):
        images_list = []
        for image in images:
            if len(image.filename):
                folder = 'media/product/'
                if not os.path.exists(folder):
                    os.mkdir(folder)
                file_url = folder + image.filename
                with open(file_url, "wb") as buffer:
                    shutil.copyfileobj(image.file, buffer)
                    images_list.append(models.ProductImage(product_id=product_id, image=file_url))

        db.add_all(images_list)
        db.commit()


@product_api.post('/add', name='product_add')
async def product_add(
        request: Request,
        form: ProductForm = Depends(ProductForm.as_form),
        db: Session = Depends(get_db),
        current_user=Depends(manager)
):
    user = db.query(models.Users).filter(models.Users.id == request.state.user.id).first()
    data = form.dict(exclude_none=True)
    images = data.pop('images')
    data.update({'author_id': current_user.id})
    product = models.Product(**data)
    db.add(product)
    db.commit()
    save_image(images, product.id, db)
    context = {
        'request': request,
        'user': user
    }
    return templates.TemplateResponse('products/product-add.html', context)


@product_api.get('/settings/{id}', name='edit_profile')
async def settings(request: Request, id: int, db: Session = Depends(get_db)):
    data = db.query(models.Users).filter(models.Users.id == id).first()
    # print(data.image)
    # print(data.banner)
    print(data.name)
    print(data.image)
    context = {
        'request': request,
        'data': data,
    }
    return templates.TemplateResponse('settings/settings.html', context)


@product_api.post('/settings/{pk}', name='edit_profile')
async def settings(request: Request, pk: int, db: Session = Depends(get_db),
                   form: EditForm = Depends(EditForm.as_form)):
    data = form.dict(exclude_unset=True)
    if len(form.image.filename):
        file_url = 'media/' + form.image.filename
        with open(file_url, "wb") as buffer:
            shutil.copyfileobj(form.image.file, buffer)
        data.update({'image': file_url})
    query = update(Users).where(Users.id == pk).values(name=form.name,
                                                       email=form.email,
                                                       image=data['image'])
    db.execute(query)
    db.commit()
    return RedirectResponse(url='/', status_code=HTTP_303_SEE_OTHER)


@product_api.post('/card/{product_id}/{user_id}', name='card')
async def card(request: Request, product_id: int, user_id: int, db: Session = Depends(get_db)):
    query = db.query(models.Card).filter(models.Card.product_id == product_id).first()
    print(query)
    if query:
        data = update(models.Card).where(models.Card.product_id == product_id).values(product_id=product_id,
                                                                                      user_id=user_id,
                                                                                      total=query.total + 1)
        db.execute(data)
        db.commit()
        return RedirectResponse(url='/', status_code=HTTP_303_SEE_OTHER)
    else:
        db.add(models.Card(user_id=user_id, product_id=product_id,total=1))
        db.commit()
        return RedirectResponse(url='/', status_code=HTTP_303_SEE_OTHER)


@product_api.get('/card_list', name='card_list')
async def card_list(request: Request, db: Session = Depends(get_db)):
    card = db.query(models.Card).where(models.Card.user_id == request.state.user.id).all()
    c = 0
    total = 0
    for i in card:
        c += i.product.price
        total += i.total
    # print(c)
    # for i in card:
    #     print(i.product.name)
    context = {
        'request': request,
        'card': card,
        'count': len(card),
        'sum': c,
        'total': total
    }
    return templates.TemplateResponse('products/shopping-cart.html', context)


@product_api.post('/card_list/{id}', name='remove_card')
async def card_remove(request: Request, id: int, db: Session = Depends(get_db)):
    print(id)
    data = db.query(models.Card).filter(models.Card.product_id == id).first()
    print(data.id)
    db.delete(data)
    db.commit()
    context = {
        "request": request
    }
    return RedirectResponse(url='/card_list', status_code=HTTP_303_SEE_OTHER)


@product_api.get('/like')
async def like(request: Request, db: Session = Depends(get_db)):
    card = db.query(models.Like).where(models.Like.user_id == request.state.user.id).all()
    for i in card:
        print(i.product.category.name)
    context = {
        'request': request,
        'card': card,
    }
    return templates.TemplateResponse('products/liked-products.html', context)


@product_api.post('/like/{product_id}/{user_id}', name='like')
async def card(request: Request, product_id: int, user_id: int, db: Session = Depends(get_db)):
    query = db.query(models.Like).filter(models.Like.product_id == product_id).first()
    print(query)
    if query:
        db.delete(query)
        db.commit()
        return RedirectResponse(url='/', status_code=HTTP_303_SEE_OTHER)
    else:
        db.add(models.Like(user_id=user_id, product_id=product_id, total=1))
        db.commit()
        return RedirectResponse(url='/', status_code=HTTP_303_SEE_OTHER)


@product_api.post('/like_list/{product_id}/{user_id}', name='like_list')
async def card(request: Request, product_id: int, user_id: int, db: Session = Depends(get_db)):
    query = db.query(models.Like).filter(models.Like.product_id == product_id).first()
    if query:
        db.delete(query)
        db.commit()
        return RedirectResponse(url='/like', status_code=HTTP_303_SEE_OTHER)


@product_api.get('/review', name='review')
async def card_list(request: Request, db: Session = Depends(get_db)):
    card = db.query(models.Card).where(models.Card.user_id == request.state.user.id).all()
    c = 0
    total = 0
    for i in card:
        c += i.product.price
        total += i.total
    # print(c)
    # for i in card:
    #     print(i.product.name)
    context = {
        'request': request,
        'card': card,
        'count': len(card),
        'sum': c,
        'total': total
    }
    return templates.TemplateResponse('products/shopping-cart.html', context)


@product_api.get('/search')
def search(request: Request, query: Optional[str], db: Session = Depends(get_db), offset: int = 0, limit: int = 6):
    data = db.query(models.Product).filter(models.Product.name.contains(query)).all()
    user = db.query(models.Users).filter(models.Users.id == request.state.user.id).first()
    # products = db.query(models.Product).order_by(-models.Product.id).all()
    for i in data:
        print(i.name)
    count = db.query(models.Product).count()
    context = {
        'request': request,
        'products': data,
        'user': user,
        'limit': limit,
        'offset': offset,
        'counter': count
    }
    return templates.TemplateResponse('products/product-list.html', context)


@product_api.post('/review/{product_id}/',name='revieew')
def review(request: Request, product_id: int, db: Session = Depends(get_db),
           form: ReviewForm = Depends(ReviewForm.as_form)
           ):
    data = form.dict(exclude_none=True)
    query = models.Review(title=form.title, text=form.text, product_id=product_id,
                          user_id=request.state.user.id)
    db.add(query)
    db.commit()


@product_api.post('/star/{product_id}/{count}',name='star')
def star(request: Request,product_id: int, count: int, form: StarForm = Depends(StarForm.as_form), db: Session = Depends(get_db)):
    data = form.dict(exclude_none=True)
    query = update(models.Review).filter(product_id == models.Review.product_id).values(
        star = count,
        user_id = request.state.user.id,
        product_id = product_id
    )
    db.execute(query)
    db.commit()
    return RedirectResponse(url='/',status_code=HTTP_303_SEE_OTHER)