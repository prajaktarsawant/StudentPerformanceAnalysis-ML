from sqlalchemy.orm import Session
from ..models.item import Item
from ..schemas.item import ItemCreate

def get_item(db: Session, item_id: int):
    return db.query(Item).filter(Item.id == item_id).first()

def get_items(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Item).offset(skip).limit(limit).all()

def create_item(db: Session, item_in: ItemCreate):
    db_item = Item(name=item_in.name, description=item_in.description)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item