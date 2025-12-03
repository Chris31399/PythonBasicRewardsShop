# business_layer.py
# Business objects + service logic:
# - Load customers & rewards
# - Redeem rewards
# - Admin CRUD: add/delete customers & rewards
# - Employee operations: issue points, process orders

from dataclasses import dataclass
from typing import List, Optional

import data_layer

@dataclass
class Customer:
    id: int
    name: str
    email: str
    points: int

@dataclass
class Reward:
    id: int
    name: str
    cost: int

@dataclass
class OrderSummary:
    id: int
    customer_id: int
    customer_name: str
    reward_id: int
    reward_name: str
    quantity: int
    points_spent: int
    status: str
    order_time: str

class RewardShopService:
    """
    Business logic tier.
    Handles loading domain objects and applying business rules.
    """

    # ---------- Load data as business objects ----------
    def get_customers(self) -> List[Customer]:
        rows = data_layer.get_all_customers()
        return [
            Customer(id=row[0], name=row[1], email=row[2], points=row[3])
            for row in rows
        ]

    def get_rewards(self) -> List[Reward]:
        rows = data_layer.get_all_rewards()
        return [
            Reward(id=row[0], name=row[1], cost=row[2])
            for row in rows
        ]

    def get_customer(self, customer_id: int) -> Optional[Customer]:
        row = data_layer.get_customer_by_id(customer_id)
        if not row:
            return None
        return Customer(id=row[0], name=row[1], email=row[2], points=row[3])

    def get_reward(self, reward_id: int) -> Optional[Reward]:
        row = data_layer.get_reward_by_id(reward_id)
        if not row:
            return None
        return Reward(id=row[0], name=row[1], cost=row[2])

    # ---------- Core business rule: redeem reward ----------

    def redeem_reward(self, customer_id: int, reward_id: int, quantity: int):
        """
        Deducts points from the customer and records an order with status 'pending',
        if they have enough points. Raises ValueError if rules are violated.
        """
        if quantity < 1:
            raise ValueError("Quantity must be at least 1.")

        customer = self.get_customer(customer_id)
        if not customer:
            raise ValueError("Customer not found.")

        reward = self.get_reward(reward_id)
        if not reward:
            raise ValueError("Reward not found.")

        total_cost = reward.cost * quantity

        if customer.points < total_cost:
            raise ValueError(
                f"{customer.name} does not have enough points. "
                f"Has {customer.points}, needs {total_cost}."
            )

        # Compute new point balance
        new_points = customer.points - total_cost

        # Persist changes in the data tier
        data_layer.update_customer_points(customer_id, new_points)
        # status will default to 'pending' inside insert_order
        data_layer.insert_order(
            customer_id=customer_id,
            reward_id=reward_id,
            quantity=quantity,
            points_spent=total_cost,
        )

        # Return the updated Customer object and some info
        updated_customer = self.get_customer(customer_id)
        return updated_customer, reward, total_cost

    # ---------- Admin operations ----------

    def add_customer(self, name: str, email: str, points: int):
        """
        Create a new customer, with simple validation.
        """
        name = name.strip()
        email = email.strip()

        if not name:
            raise ValueError("Name is required.")
        if not email or "@" not in email:
            raise ValueError("A valid email is required.")
        if points < 0:
            raise ValueError("Points cannot be negative.")

        data_layer.insert_customer(name, email, points)

    def delete_customer(self, customer_id: int):
        """
        Delete a customer (and any related orders via FK, if configured).
        """
        data_layer.delete_customer(customer_id)

    def add_reward(self, name: str, cost: int):
        """
        Create a new reward.
        """
        name = name.strip()
        if not name:
            raise ValueError("Reward name is required.")
        if cost <= 0:
            raise ValueError("Reward cost must be greater than 0.")

        data_layer.insert_reward(name, cost)

    def delete_reward(self, reward_id: int):
        """
        Delete a reward (and any related orders via FK, if configured).
        """
        data_layer.delete_reward(reward_id)

    # ---------- Employee operations: pending orders + issuing points ----------

    def get_pending_orders(self) -> List[OrderSummary]:
        rows = data_layer.get_pending_orders_with_details()
        return [
            OrderSummary(
                id=row[0],
                customer_id=row[1],
                customer_name=row[2],
                reward_id=row[3],
                reward_name=row[4],
                quantity=row[5],
                points_spent=row[6],
                status=row[7],
                order_time=row[8],
            )
            for row in rows
        ]

    def issue_points(self, customer_id: int, points: int) -> Customer:
        """
        Add points to a customer's account.
        """
        if points <= 0:
            raise ValueError("Points to add must be greater than 0.")

        customer = self.get_customer(customer_id)
        if not customer:
            raise ValueError("Customer not found.")

        new_points = customer.points + points
        data_layer.update_customer_points(customer_id, new_points)
        updated = self.get_customer(customer_id)
        return updated

    def fulfill_order(self, order_id: int):
        """
        Mark an order as fulfilled. Points were already deducted when the order was created,
        so we just flip the status.
        """
        row = data_layer.get_order_by_id(order_id)
        if not row:
            raise ValueError("Order not found.")

        status = row[6]
        if status != "pending":
            raise ValueError(f"Order is not pending (current status: {status}).")

        data_layer.update_order_status(order_id, "fulfilled")

    def cancel_order(self, order_id: int) -> Customer:
        """
        Cancel an order:
          - Refund points_spent back to the customer's account.
          - Mark the order as 'cancelled'.
        Returns the updated Customer object.
        """
        row = data_layer.get_order_by_id(order_id)
        if not row:
            raise ValueError("Order not found.")

        order_id_db, customer_id, reward_id, quantity, points_spent, order_time, status = row
        if status != "pending":
            raise ValueError(f"Order is not pending (current status: {status}).")

        customer = self.get_customer(customer_id)
        if not customer:
            raise ValueError("Customer not found for this order.")

        # Refund points
        new_points = customer.points + points_spent
        data_layer.update_customer_points(customer_id, new_points)

        # Update order status
        data_layer.update_order_status(order_id, "cancelled")

        # Return updated customer
        updated_customer = self.get_customer(customer_id)
        return updated_customer
