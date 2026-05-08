"""
Test suite for the Cart component.
Structure:
    - One test class per group of related tests (AddItem, Checkout, etc.)
    - Each class has a setUp() method that runs BEFORE every test in that class.
      This gives every test a fresh database, a clean member, and a clean cart.
    - Each test is a method starting with "test_".
    - tearDown() runs AFTER every test to clean up.
"""

import unittest
from app import app, db
from models.users import Member, MemberStatus
from models.Items import Book, Computer, Condition
from models.Cart import Cart
from models.Fine import Fine
from models.Transaction import Transaction, TransactionType


class CartTestBase(unittest.TestCase):
    """
    Base class with shared setUp/tearDown logic.
    Every test class below inherits from this so they all get the same
    clean-database behavior without repeating the code.
    """

    def setUp(self):
        # Point the app at an in-memory database so tests don't touch library.db
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True

        # Push the app context so database operations work
        self.app_context = app.app_context()
        self.app_context.push()

        # Build fresh empty tables
        db.create_all()

        # Create a clean test member
        self.member = Member(
            name="Test User",
            email="test@test.com",
            password="password123"
        )
        db.session.add(self.member)
        db.session.commit()

        # Create a clean test book with 2 copies available
        self.book = Book(
            title="Test Book", qty=2, author="Test Author",
            isbn=None, publisher=None, genre=None,
            edition=None, description=None
        )
        db.session.add(self.book)
        db.session.commit()

        # Get the member's cart (creates one if it doesn't exist)
        self.cart = Cart.get_or_create(self.member.user_id)

    def tearDown(self):
        # Clean up the database after each test
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # Small helper methods used by multiple test classes
    def make_extra_book(self, title="Extra Book"):
        """Create and save a new book, return it."""
        book = Book(
            title=title, qty=1, author="Author",
            isbn=None, publisher=None, genre=None,
            edition=None, description=None
        )
        db.session.add(book)
        db.session.commit()
        return book

    def give_member_a_loan(self, book, tx_type=TransactionType.LOAN):
        """Attach an active loan transaction to the member for a given book."""
        tx = Transaction(
            user_id=self.member.user_id,
            item_id=book.item_id,
            transaction_type=tx_type,
            item_type="Book"
        )
        db.session.add(tx)
        db.session.commit()
        return tx


# ============================================================
# Tests for Cart.add_item()
# ============================================================

class TestAddItem(CartTestBase):

    def test_add_item_success(self):
        """Adding a valid item should put it in the cart."""
        self.cart.add_item(self.book.item_id)
        self.assertEqual(self.cart.item_count(), 1)

    def test_add_item_not_found(self):
        """Adding a fake item_id should raise ValueError."""
        with self.assertRaises(ValueError):
            self.cart.add_item("not-a-real-id")

    def test_add_duplicate_item(self):
        """Adding the same item twice should raise ValueError."""
        self.cart.add_item(self.book.item_id)
        with self.assertRaises(ValueError):
            self.cart.add_item(self.book.item_id)


# ============================================================
# Tests for Cart.item_count() and Cart.clear_cart()
# ============================================================

class TestItemCountAndClear(CartTestBase):

    def test_empty_cart_has_zero_items(self):
        """A new cart starts with 0 items."""
        self.assertEqual(self.cart.item_count(), 0)

    def test_clear_cart_removes_everything(self):
        """Clearing a cart with items should leave it empty."""
        self.cart.add_item(self.book.item_id)
        second_book = self.make_extra_book("Second Book")
        self.cart.add_item(second_book.item_id)
        self.assertEqual(self.cart.item_count(), 2)

        self.cart.clear_cart()
        self.assertEqual(self.cart.item_count(), 0)


# ============================================================
# Tests for Cart.checkout() — basic functionality
# ============================================================

class TestCheckoutBasics(CartTestBase):

    def test_checkout_loans_available_item(self):
        """An available item should become a loan transaction."""
        self.cart.add_item(self.book.item_id)
        transactions, reservations = self.cart.checkout()

        self.assertEqual(len(transactions), 1)
        self.assertEqual(len(reservations), 0)
        self.assertEqual(self.cart.item_count(), 0)  # cart is cleared

    def test_checkout_reserves_unavailable_item(self):
        """An unavailable item should become a reservation."""
        # Make the book unavailable by zeroing its quantity
        self.book.available_qty = 0
        db.session.commit()

        self.cart.add_item(self.book.item_id)
        transactions, reservations = self.cart.checkout()

        self.assertEqual(len(transactions), 0)
        self.assertEqual(len(reservations), 1)

    def test_checkout_decreases_item_quantity(self):
        """Loaning an item should reduce its available_qty by 1."""
        starting_qty = self.book.available_qty
        self.cart.add_item(self.book.item_id)
        self.cart.checkout()

        db.session.refresh(self.book)
        self.assertEqual(self.book.available_qty, starting_qty - 1)


# ============================================================
# Tests for Cart.checkout() — error handling
# ============================================================

class TestCheckoutErrors(CartTestBase):

    def test_empty_cart_cannot_checkout(self):
        """Checking out an empty cart should raise ValueError."""
        with self.assertRaises(ValueError):
            self.cart.checkout()

    def test_member_with_unpaid_fine_blocked(self):
        """A member with an unpaid fine should not be able to check out."""
        # Need a transaction to attach a fine to
        tx = self.give_member_a_loan(self.book)
        fine = Fine(
            user_id=self.member.user_id,
            transaction_id=tx.transaction_id,
            reason="Test fine",
            amount=5.0
        )
        db.session.add(fine)
        db.session.commit()

        other_book = self.make_extra_book("Other Book")
        self.cart.add_item(other_book.item_id)

        with self.assertRaises(ValueError):
            self.cart.checkout()

    def test_suspended_member_blocked(self):
        """A suspended member should not be able to check out.

        NOTE: EXPECTED TO FAIL with current code.
        Cart.checkout() does not check member.status, which is a bug.
        Member.loan_items() checks it, but the Cart path bypasses that method.
        """
        self.member.status = MemberStatus.SUSPENDED
        db.session.commit()

        self.cart.add_item(self.book.item_id)

        with self.assertRaises(ValueError):
            self.cart.checkout()

    def test_deleted_item_blocks_checkout(self):
        """If an item is deleted while in a cart, checkout should fail cleanly."""
        self.cart.add_item(self.book.item_id)
        db.session.delete(self.book)
        db.session.commit()

        with self.assertRaises(ValueError):
            self.cart.checkout()


# ============================================================
# Tests for Cart.checkout() — loan limit boundaries
# ============================================================

class TestCheckoutLoanLimits(CartTestBase):

    def test_at_loan_limit_still_works(self):
        """3 active loans + 1 new = 4 total (the limit). Should succeed."""
        for i in range(3):
            existing = self.make_extra_book(f"Existing {i}")
            self.give_member_a_loan(existing)

        fourth_book = self.make_extra_book("Fourth Book")
        self.cart.add_item(fourth_book.item_id)

        transactions, _ = self.cart.checkout()
        self.assertEqual(len(transactions), 1)

    def test_over_loan_limit_fails(self):
        """4 active loans + 1 new = 5 total (over limit). Should fail."""
        for i in range(4):
            existing = self.make_extra_book(f"Existing {i}")
            self.give_member_a_loan(existing)

        fifth_book = self.make_extra_book("Fifth Book")
        self.cart.add_item(fifth_book.item_id)

        with self.assertRaises(ValueError):
            self.cart.checkout()

    def test_renewed_loans_should_count(self):
        """Renewed loans should count toward the limit, just like regular loans.

        NOTE: EXPECTED TO FAIL with current code.
        Cart's loan count query only looks for TransactionType.LOAN,
        ignoring TransactionType.RENEWED. This lets members with renewed
        loans bypass the 4-item limit.
        """
        for i in range(4):
            existing = self.make_extra_book(f"Renewed {i}")
            self.give_member_a_loan(existing, tx_type=TransactionType.RENEWED)

        fifth_book = self.make_extra_book("Fifth Book")
        self.cart.add_item(fifth_book.item_id)

        with self.assertRaises(ValueError):
            self.cart.checkout()

    def test_computer_limit(self):
        """A member with 1 computer on loan + 1 computer in cart should fail."""
        # Existing computer loan
        old_computer = Computer(
            title="Old Laptop", serial_number="SN111",
            os="Linux", condition=Condition.GOOD
        )
        db.session.add(old_computer)
        db.session.commit()
        tx = Transaction(
            user_id=self.member.user_id,
            item_id=old_computer.item_id,
            transaction_type=TransactionType.LOAN,
            item_type="Computer"
        )
        db.session.add(tx)
        db.session.commit()

        # Second computer in cart
        new_computer = Computer(
            title="New Laptop", serial_number="SN222",
            os="Windows", condition=Condition.GOOD
        )
        db.session.add(new_computer)
        db.session.commit()
        self.cart.add_item(new_computer.item_id)

        with self.assertRaises(ValueError):
            self.cart.checkout()


# ============================================================
# Run tests when file is executed directly
# ============================================================

if __name__ == "__main__":
    unittest.main()
