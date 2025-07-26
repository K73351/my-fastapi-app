from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import update, select, insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.backend.db_depends import get_db
from app.schemas import CreateProduct
from .auth import get_current_user
from app.models import *
from typing import Annotated
from slugify import slugify


router = APIRouter(prefix='/products', tags=['products'])


@router.get('/')
async def all_products(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.scalars(select(Product).where(Product.is_active == True, Product.stock > 0))
    products = result.all()

    if not products:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There are no product'
        )

    return products


@router.post('/create')
async def create_product(db: Annotated[AsyncSession, Depends(get_db)], get_user: Annotated[dict, Depends(get_current_user)], create_product: CreateProduct):
    if get_user.get('is_admin') or get_user.get('is_supplier'):
        await db.execute(insert(Product).values(name=create_product.name,
                                          slug=slugify(create_product.name),
                                          description=create_product.description,
                                          price=create_product.price,
                                          image_url=create_product.image_url,
                                          stock=create_product.stock,
                                          category_id=create_product.category,
                                          rating=0.0,
                                          supplier_id=get_user.get('id')))
        await db.commit()

        return {
            'status_code': status.HTTP_201_CREATED,
            'transaction': 'Successful'
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='You are not authorized to use this method'
        )


@router.get('/{category_slug}')
async def product_by_category(category_slug: str, db: Annotated[AsyncSession, Depends(get_db)]):
    category = await db.scalar(select(Category).where(Category.slug == category_slug))

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Category not found'
        )

    category_ids = [category.id]

    subcategories_ids = await db.scalars(select(Category.id).where(Category.parent_id == category.id))
    subcategories_ids = subcategories_ids.all()
    category_ids.extend(subcategories_ids)

    products = await db.scalars(
        select(Product).where(
            Product.category_id.in_(category_ids),
            Product.is_active == True,
            Product.stock > 0
        )
    )
    products = products.all()

    if not products:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There are no products'
        )

    return products


@router.get('/detail/{product_slug}')
async def product_detail(product_slug: str, db: Annotated[AsyncSession, Depends(get_db)]):
    product = await db.scalar(select(Product).where(Product.slug == product_slug,
                                              Product.is_active == True,
                                              Product.stock > 0))

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There are no product'
        )

    return product


@router.put('/detail/{product_slug}')
async def update_product(product_slug: str, db: Annotated[AsyncSession, Depends(get_db)], get_user: Annotated[dict, Depends(get_current_user)], update_product: CreateProduct):
    product = await db.scalar(select(Product).where(Product.slug == product_slug))

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There is no product found'
        )

    if get_user.get('is_admin') or (get_user.get('is_supplier') and get_user.get('id') == product.supplier_id):
        await db.execute(update(Product).where(Product.slug == product_slug).values(name=update_product.name,
                                          slug=slugify(update_product.name),
                                          description=update_product.description,
                                          price=update_product.price,
                                          image_url=update_product.image_url,
                                          stock=update_product.stock,
                                          category_id=update_product.category,
                                          rating=0.0))
        await db.commit()

        return {
            'status_code': status.HTTP_200_OK,
            'transaction': 'Product update is successful'
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='You are not authorized to use this method'
        )

@router.delete('/delete')
async def delete_product(db: Annotated[AsyncSession, Depends(get_db)], get_user: Annotated[dict, Depends(get_current_user)], product_id: int):
    product = await db.scalar(select(Product).where(Product.id == product_id))

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There is no product found'
        )

    if get_user.get('is_admin') or (get_user.get('is_supplier') and get_user.get('id') == product.supplier_id):
        await db.execute(update(Product).where(Product.id == product_id).values(is_active=False))
        await db.commit()
        return {
            'status_code': status.HTTP_200_OK,
            'transaction': 'Product delete is successful'
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='You are not authorized to use this method'
        )