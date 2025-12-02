# business_layer.py
# This layer defines business objects and rules: customers, rewards and a service that handles “redeem reward” logic safely.
from dataclasses import dataclass
from typing import List

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


class RewardShopService:
    """
    Business logic tier.
    Handles loading domain objects and applying business rules.
    """

    # ---------- Load data as business objects ----------

    def get_customers(self) -> List[Customer]:
        rows = data_layer.get_all_customers()
        return [Customer(id=row[0], name=row[1], email=row[2], points=row[3])
                for row in rows]

    def get_rewards(self) -> List[Reward]:
        rows = data_layer.get_all_rewards()
        return [Reward(id=row[0], name=row[1], cost=row[2])
                for row in rows]

    def get_customer(self, customer_id: int) -> Customer | None:
        row = data_layer.get_customer_by_id(customer_id)
        if not row:
            return None
        return Customer(id=row[0], name=row[1], email=row[2], points=row[3])

    def get_reward(self, reward_id: int) -> Reward | None:
        row = data_layer.get_reward_by_id(reward_id)
        if not row:
            return None
        return Reward(id=row[0], name=row[1], cost=row[2])

    # ---------- Core business rule: redeem reward ----------

    def redeem_reward(self, customer_id: int, reward_id: int, quantity: int):
        """
        Deducts points from the customer and records an order, if they have enough points.
        Raises ValueError with a message if business rules are violated.
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
        data_layer.insert_order(
            customer_id=customer_id,
            reward_id=reward_id,
            quantity=quantity,
            points_spent=total_cost
        )

        # Return the updated Customer object and some info
        updated_customer = self.get_customer(customer_id)
        return updated_customer, reward, total_cost
