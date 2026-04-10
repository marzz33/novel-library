from app import db
from datetime import datetime, timezone, timedelta
import uuid

def utcnow():
  return datetime.now(timezone.utc)

class CartItems(db.Model):

  __tablename__ = 'cart_items'
  
  id = db.Column(db.Integer, primary_key = True)
  cart_id = db.Column(db.String(80), db.ForeignKey('Carts.cart_id'), nullable = False)
  cart_item_id = db.Column(db.String(80), unique = True, nullable = False)
  item_id = db.Column(db.String(80), db.ForeignKey('Items.item_id'), nullable = False)
  added_on = db.Column(db.DateTime, default = utcnow)

  item = db.relationship('Item', lazy = True)

  def __init__(self, cart_id, item_id, action):
    self.cart_id = cart_id
    self.cart_item_id = str(uuid.uuid4())
    self.item_id = item_id
    self.added_on = utcnow()

  def to_dict(self):
    return {
      "cart_item_id": self.cart_item_id,
      "item_id": self.item_id,
      "title": self.item.title if self.item else None,
      "item_type": self.item.item_type if self.item else None,
      "added_on": self.added_on.isoformat()
    }
  
class Cart(db.Model):


    
  
