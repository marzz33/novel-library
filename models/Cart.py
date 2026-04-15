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

  __tablename__ = 'Carts'

  id = db.Column(db.Integer, primary_key = True)
  cart_id = db.Column(db.String(80), unique = True, nullable = False)
  user_id = db.Column(db.String(80), db.ForeignKey('users.user_id'), nullable = False)
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

  # This function allows users to add items to their cart, it will check if the item exists
  # and if it is already in the cart before adding it
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
  
  # This function allows users to remove items from their cart, it will check if the item
  # exists in the cart before attempting to remove it
  def remove_item(self, cart_item_id):
    cart_item = CartItems.query.filter_by(cart_item_id = cart_item_id, cart_id = self.cart_id).first()
    if not cart_item:
      raise ValueError("Cart item not found.")
    
    db.session.delete(cart_item)
    db.session.commit()
    return True

  # This function allows users to clear their cart, it will delete all items associated with the cart_id
  def clear_cart(self):
    CartItems.query.filter_by(cart_id = self.cart_id).delete()
    db.session.commit()
    return True
  
  # This function allows users to view the items in their cart, it will return a list of CartItems associated with the cart_id
  def view_cart(self):
    return CartItems.query.filter_by(cart_id = self.cart_id).all()
  
  # This function returns the number of items in the cart, it will count the number of CartItems associated with the cart_id
  def item_count(self):
    return CartItems.query.filter_by(cart_id = self.cart_id).count()

  # Validates EVERY item in the cart before loaning ANY of them.
    # If any item fails validation (unavailable, over loan limit, unpaid fines),
    # the whole checkout is rejected and nothing is loaned.
  def checkout(self):
      from models.Items import Item
      from models.users import Member
      from models.Transaction import Transaction, TransactionType, TransactionStatus

      member = Member.query.filter_by(user_id = self.user_id).first()
      if not member:
          raise ValueError("Member not found.")

  # Block checkout entirely if the member has any unpaid fines
      if member.has_unpaid_fines():
          raise ValueError("You have unpaid fines. Please resolve them before checking out.")

      cart_list = self.view_cart()
      if not cart_list:
        raise ValueError("Your cart is empty.")
      
      # Cart will allow members to check out available items and reserve unavailable items in the same transaction,
      # but it will validate all items first before processing any loans or reservations.
      to_loan = []
      to_reserve = []

      for list in cart_list:
        item = Item.query.filter_by(item_id = list.item_id).first()
        if not item:
          raise ValueError(f"An item in your cart no longer exists. Please remove it and try again.")
        
        if item.check_availability():
          to_loan.append(item)
        else:
          to_reserve.append(item)

      # Check all items for availability and loan limits before processing any transactions

      current_loans = Transaction.query.filter(Transaction.user_id == self.user_id,        # type: ignore
            Transaction.transaction_type == TransactionType.LOAN,           # type: ignore
            db.or_(
              Transaction.status == TransactionStatus.ACTIVE,
              Transaction.status == TransactionStatus.OVERDUE
            )
      ).count()

      # Loan limit check: if we were to loan all available items in the cart, would the member exceed their loan limit?
      if current_loans + len(to_loan) > member.max_loanable_items:
        raise ValueError(f"Checking out would exceed your loan limit of {member.max_loanable_items} items." f"You currently have {current_loans} active loans.")

      computer_count = sum(1 for item in to_loan if item.item_type == "Computer")
      if computer_count > 0:
        current_computers = Transaction.query.filter(Transaction.user_id == self.user_id,                            # type: ignore
            Transaction.transaction_type == TransactionType.LOAN,           # type: ignore
            Transaction.item_type == "Computer",                            # type: ignore
            db.or_(
                Transaction.status == TransactionStatus.ACTIVE,
                Transaction.status == TransactionStatus.OVERDUE
            )
        ).count()

        if current_computers + computer_count > member.max_loanable_computers:
          raise ValueError(f"Checking out would exceed your computer loan limit of {member.max_loanable_computers} items." f"You currently have {current_computers} active computer loans.")

      # If we made it here, all items passed validation and we can proceed with checkout
      transactions = []
      reservations = []

      try:
        for item in to_loan:
          success = item.loan(self.user_id)
          transactions.append(success)

        for item in to_reserve:
          success = item.reserve(self.user_id)
          reservations.append(success)
      except Exception:
        # If any unexpected error occurs during processing (e.g. database error), we want to roll back the entire transaction to prevent partial checkouts
        db.session.rollback()
        raise ValueError("An error occurred during checkout. Please try again.")
      
      db.session.commit()
      self.clear_cart()
      return transactions, reservations

    # Static helper: get a member's cart, creating it if it doesn't exist yet.
    # Use this in routes instead of querying Cart directly so members never
    # hit a "no cart found" error on their first add.
  @staticmethod
  def get_or_create(user_id: str):
    cart = Cart.query.filter_by(user_id=user_id).first()
    if not cart:
      cart = Cart(user_id=user_id)
      db.session.add(cart)
      db.session.commit()
    return cart

  def to_dict(self):
    return {
      "cart_id":    self.cart_id,
      "user_id":    self.user_id,
      "created_on": self.created_on.isoformat(),
      "item_count": self.item_count(),
      "items":      [line.to_dict() for line in self.view_cart()]
    }