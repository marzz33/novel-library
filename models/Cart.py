from app import db
from datetime import datetime, timezone, timedelta
import uuid

def utcnow():
  return datetime.now(timezone.utc)

class CartItems(db.Model):

  __tablename__ = 'Cart_items'
  
  id = db.Column(db.Integer, primary_key = True)
  cart_id = db.Column(db.String(80), db.ForeignKey('Carts.cart_id'), nullable = False)
  cart_item_id = db.Column(db.String(80), unique = True, nullable = False)
  item_id = db.Column(db.String(80), db.ForeignKey('Items.item_id'), nullable = False)
  added_on = db.Column(db.DateTime, default = utcnow)

  item = db.relationship('Item', lazy = True)

  def __init__(self, cart_id, item_id):
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

  __tablename__ = 'Cart'

  id = db.Column(db.Integer, primary_key = True)
  cart_id = db.Column(db.String(80), unique = True, nullable = False)
  user_id = db.Column(db.String(80), db.ForeignKey('Users.user_id'), nullable = False)
  created_on = db.Column(db.DateTime, default = utcnow)

  # This relationship allows us to easily access the user associated with this cart, as well as the items in the cart.
  # cascade = 'all, delete-orphan' ensures that when a cart is deleted, all associated CartItems are also deleted to prevent orphaned records
  # backref = db.backref('cart', uselist = False) allows us to access the cart from the user model using user.cart

  user = db.relationship('User', backref = db.backref('cart', uselist = False))
  items = db.relationship('CartItems', backref = 'cart', cascade = 'all, delete-orphan', lazy  = True)

  def __init__(self, user_id):
    self.cart_id = str(uuid.uuid4())
    self.user_id = user_id
    self.created_on = utcnow()

  def add_item(self, item_id):
    from models.Items import Item

    item = Item.query.filter_by(item_id = item_id).first()
    if not item:
      raise ValueError("Item not found.")
    
    duplicate = CartItems.query.filter_by(cart_id = self.cart_id, item_id = item_id).first()
    if duplicate:
      raise ValueError(f"{item.title} already in cart.")

    cart_item = CartItems(cart_id = self.cart_id, item_id = item_id)
    db.session.add(cart_item)
    db.session.commit()
    return cart_item
  
  