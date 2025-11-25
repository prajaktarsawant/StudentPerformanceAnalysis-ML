from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ...core.database import get_db
from ...crud import crud_item
from ...schemas import item as item_schemas

# API router instance
router = APIRouter()

@router.post("/", response_model=item_schemas.Item, status_code=status.HTTP_201_CREATED)
def create_item_api(
    item_in: item_schemas.ItemCreate, 
    db: Session = Depends(get_db)
):
    """Create a new item (JSON endpoint)."""
    return crud_item.create_item(db=db, item_in=item_in)

@router.get("/", response_model=List[item_schemas.Item])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retrieve a list of items."""
    items = crud_item.get_items(db, skip=skip, limit=limit)
    return items

@router.get("/{item_id}", response_model=item_schemas.Item)
def read_item(item_id: int, db: Session = Depends(get_db)):
    """Retrieve a single item by ID."""
    db_item = crud_item.get_item(db, item_id=item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item