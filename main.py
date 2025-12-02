# main.py
# This is the GUI that lets you pick a customer, pick a reward and enter quantities
# Then redeems the reward if there are enough points and shows message boxes with success/failure

import tkinter as tk
from tkinter import ttk, messagebox

import data_layer
from business_layer import RewardShopService


class RewardShopApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Rewards Shop (Python 3-Tier Demo)")
        self.service = RewardShopService()

        # Keep current selections
        self.customers = []
        self.rewards = []
        self.selected_customer_id = None
        self.selected_reward_id = None

        # Build the GUI
        self._build_ui()

        # Load initial data
        self.load_customers()
        self.load_rewards()

    # ---------- UI Building ----------

    def _build_ui(self):
        self.root.geometry("700x400")

        # Frames (left: customers, right: rewards + redeem)
        left_frame = ttk.Frame(self.root, padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_frame = ttk.Frame(self.root, padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # ----- Customers list -----
        ttk.Label(left_frame, text="Customers").pack(anchor="w")
        self.customer_list = tk.Listbox(left_frame, height=10)
        self.customer_list.pack(fill=tk.BOTH, expand=True, pady=5)
        self.customer_list.bind("<<ListboxSelect>>", self.on_customer_selected)

        self.customer_points_label = ttk.Label(left_frame, text="Points: -")
        self.customer_points_label.pack(anchor="w", pady=5)

        ttk.Button(left_frame, text="Refresh Customers", command=self.load_customers).pack(
            anchor="w", pady=5
        )

        # ----- Rewards list -----
        ttk.Label(right_frame, text="Rewards").pack(anchor="w")
        self.reward_list = tk.Listbox(right_frame, height=10)
        self.reward_list.pack(fill=tk.BOTH, expand=True, pady=5)
        self.reward_list.bind("<<ListboxSelect>>", self.on_reward_selected)

        self.reward_cost_label = ttk.Label(right_frame, text="Cost: -")
        self.reward_cost_label.pack(anchor="w", pady=5)

        # ----- Quantity + Redeem -----
        qty_frame = ttk.Frame(right_frame)
        qty_frame.pack(anchor="w", pady=10)

        ttk.Label(qty_frame, text="Quantity:").pack(side=tk.LEFT)
        self.qty_var = tk.StringVar(value="1")
        self.qty_entry = ttk.Entry(qty_frame, textvariable=self.qty_var, width=5)
        self.qty_entry.pack(side=tk.LEFT, padx=5)

        redeem_btn = ttk.Button(right_frame, text="Redeem Reward", command=self.redeem_click)
        redeem_btn.pack(anchor="w", pady=10)

    # ---------- Data Loading into UI ----------

    def load_customers(self):
        self.customers = self.service.get_customers()
        self.customer_list.delete(0, tk.END)

        for c in self.customers:
            display = f"{c.name} ({c.email}) - {c.points} pts"
            self.customer_list.insert(tk.END, display)

        self.selected_customer_id = None
        self.customer_points_label.config(text="Points: -")

    def load_rewards(self):
        self.rewards = self.service.get_rewards()
        self.reward_list.delete(0, tk.END)

        for r in self.rewards:
            display = f"{r.name} - {r.cost} pts"
            self.reward_list.insert(tk.END, display)

        self.selected_reward_id = None
        self.reward_cost_label.config(text="Cost: -")

    # ---------- Event Handlers ----------

    def on_customer_selected(self, event):
        idx = self.customer_list.curselection()
        if not idx:
            self.selected_customer_id = None
            self.customer_points_label.config(text="Points: -")
            return

        customer = self.customers[idx[0]]
        self.selected_customer_id = customer.id
        self.customer_points_label.config(
            text=f"Points: {customer.points}"
        )

    def on_reward_selected(self, event):
        idx = self.reward_list.curselection()
        if not idx:
            self.selected_reward_id = None
            self.reward_cost_label.config(text="Cost: -")
            return

        reward = self.rewards[idx[0]]
        self.selected_reward_id = reward.id
        self.reward_cost_label.config(
            text=f"Cost: {reward.cost} pts"
        )

    def redeem_click(self):
        # Validate selections
        if self.selected_customer_id is None:
            messagebox.showwarning("Missing Selection", "Please select a customer.")
            return

        if self.selected_reward_id is None:
            messagebox.showwarning("Missing Selection", "Please select a reward.")
            return

        # Validate quantity
        try:
            qty = int(self.qty_var.get())
        except ValueError:
            messagebox.showerror("Invalid Quantity", "Quantity must be a whole number.")
            return

        # Call business logic
        try:
            updated_customer, reward, total_cost = self.service.redeem_reward(
                customer_id=self.selected_customer_id,
                reward_id=self.selected_reward_id,
                quantity=qty
            )
        except ValueError as e:
            messagebox.showerror("Cannot Redeem", str(e))
            return

        # Success
        messagebox.showinfo(
            "Redeemed",
            f"{updated_customer.name} redeemed {qty} x {reward.name}\n"
            f"Total cost: {total_cost} points\n"
            f"New balance: {updated_customer.points} points"
        )

        # Refresh customers list + points label
        self.load_customers()
        # Reselect the same customer if possible
        for i, c in enumerate(self.customers):
            if c.id == updated_customer.id:
                self.customer_list.selection_set(i)
                self.customer_list.see(i)
                self.customer_points_label.config(
                    text=f"Points: {updated_customer.points}"
                )
                break


if __name__ == "__main__":
    # Initialize DB and launch app
    data_layer.init_db()

    root = tk.Tk()
    app = RewardShopApp(root)
    root.mainloop()
