from app import db
from enum import Enum
import uuid
from datetime import datetime, timezone, timedelta

def utcnow():
  return datetime.now(timezone.utc)

class CartPurpose(Enum):
  LOAN = "Loan"
  RESERVE = "Reserve"

class CartItems(db.Model):

  __tablename__ = 'cart_items'
  
  id = db.Column(db.Integer, primarykey = True)
  cart_id = db.Column(db.String(80), db.ForeignKey('carts.cart_id'), nullable = False)
  cart_item_id = db.Column(db.String(80), unique = True, nullable = False)
  item_id = db.Column(db.String(80), db.ForeignKey('items.item_id'), nullable = False)
  action = db.Column(db.Enum(CartPurpose), nullable = False)
  added_on = db.Column(db.DateTime, default = utcnow)

  item = db.relationhip('Item', lazy = True)

  def __init__(self, cart_id, item_id, action):
    self.cart_id = cart_id
    self.cart_item_id = str(uuid.uuid4())
    self.item_id = item_id
    self.action = action
    self.added_on = added_on


    
  
