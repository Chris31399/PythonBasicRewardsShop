# main.py
# GUI with three tabs: Customer, Employee, Admin.
# Customer tab: pick customer + reward, quantity, redeem (creates pending orders).
# Employee tab: issue points (left) + process pending orders (right).
# Admin tab: two-column layout to add/delete customers and rewards.

import tkinter as tk
from tkinter import ttk, messagebox

import data_layer
from business_layer import RewardShopService

print("data_layer module file:", data_layer.__file__)
print("business_layer module file:", __import__("business_layer").__file__)


class RewardShopApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Rewards Shop (Python 3-Tier Demo)")
        self.service = RewardShopService()

        # Keep current selections / cached lists
        self.customers = []
        self.rewards = []
        self.pending_orders = []
        self.selected_customer_id = None
        self.selected_reward_id = None

        # Build the GUI
        self._build_ui()

        # Load initial data
        self.load_customers()
        self.load_rewards()
        self.load_pending_orders()

    # ---------- UI Building ----------
    def _build_ui(self):
        self.root.geometry("1000x500")

        # ===== NAV BAR: TABS =====
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Three tabs: Customer / Employee / Admin
        customer_tab = ttk.Frame(notebook, padding=10)
        employee_tab = ttk.Frame(notebook, padding=10)
        admin_tab = ttk.Frame(notebook, padding=10)

        notebook.add(customer_tab, text="Customer")
        notebook.add(employee_tab, text="Employee")
        notebook.add(admin_tab, text="Admin")

        # ===========================
        # CUSTOMER TAB CONTENT
        # ===========================
        # Frames (left: customers, right: rewards + redeem)
        left_frame = ttk.Frame(customer_tab, padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_frame = ttk.Frame(customer_tab, padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # ----- Customers list -----
        ttk.Label(left_frame, text="Select a Customer", font=("Arial", 12, "bold")).pack(anchor="w")
        # exportselection=False so selecting in rewards list doesn't clear this
        self.customer_list = tk.Listbox(left_frame, height=12, exportselection=False)
        self.customer_list.pack(fill=tk.BOTH, expand=True, pady=5)
        self.customer_list.bind("<<ListboxSelect>>", self.on_customer_selected)

        self.customer_points_label = ttk.Label(left_frame, text="Points: -")
        self.customer_points_label.pack(anchor="w", pady=5)

        ttk.Button(left_frame, text="Refresh Customers", command=self.load_customers).pack(
            anchor="w", pady=5
        )

        # ----- Rewards list -----
        ttk.Label(right_frame, text="Redeem Rewards", font=("Arial", 12, "bold")).pack(anchor="w")
        self.reward_list = tk.Listbox(right_frame, height=12, exportselection=False)
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

        # ===========================
        # EMPLOYEE TAB CONTENT
        # ===========================
        emp_left = ttk.Frame(employee_tab, padding=10)
        emp_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        emp_right = ttk.Frame(employee_tab, padding=10)
        emp_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # --- Employee: Issue Points (left) ---
        ttk.Label(emp_left, text="Issue Points to Customers", font=("Arial", 12, "bold")).pack(
            anchor="w"
        )
        self.emp_customer_list = tk.Listbox(emp_left, height=12, exportselection=False)
        self.emp_customer_list.pack(fill=tk.BOTH, expand=True, pady=5)

        points_frame = ttk.Frame(emp_left)
        points_frame.pack(anchor="w", pady=5)

        ttk.Label(points_frame, text="Points to add:").pack(side=tk.LEFT)
        self.emp_points_var = tk.StringVar(value="0")
        self.emp_points_entry = ttk.Entry(points_frame, textvariable=self.emp_points_var, width=8)
        self.emp_points_entry.pack(side=tk.LEFT, padx=5)

        ttk.Button(emp_left, text="Issue Points", command=self.issue_points_click).pack(
            anchor="w", pady=10
        )

        # --- Employee: Pending Orders (right) ---
        ttk.Label(emp_right, text="Pending Orders", font=("Arial", 12, "bold")).pack(anchor="w")
        self.emp_order_list = tk.Listbox(emp_right, height=12, exportselection=False)
        self.emp_order_list.pack(fill=tk.BOTH, expand=True, pady=5)

        emp_order_btns = ttk.Frame(emp_right)
        emp_order_btns.pack(anchor="w", pady=5)

        ttk.Button(emp_order_btns, text="Fulfill Order",
                   command=self.fulfill_order_click).pack(side=tk.LEFT, padx=5)
        ttk.Button(emp_order_btns, text="Cancel Order",
                   command=self.cancel_order_click).pack(side=tk.LEFT, padx=5)

        # ===========================
        # ADMIN TAB CONTENT
        # ===========================
        # Two-column layout similar to customer tab
        admin_left = ttk.Frame(admin_tab, padding=10)
        admin_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        admin_right = ttk.Frame(admin_tab, padding=10)
        admin_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # --- Admin Customers ---
        ttk.Label(admin_left, text="Manage Customers", font=("Arial", 12, "bold")).pack(anchor="w")
        self.admin_customer_list = tk.Listbox(admin_left, height=12, exportselection=False)
        self.admin_customer_list.pack(fill=tk.BOTH, expand=True, pady=5)

        admin_cust_btns = ttk.Frame(admin_left)
        admin_cust_btns.pack(anchor="w", pady=5)

        ttk.Button(admin_cust_btns, text="Add Customer",
                   command=self.open_add_customer_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(admin_cust_btns, text="Delete Customer",
                   command=self.delete_selected_customer).pack(side=tk.LEFT, padx=5)

        # --- Admin Rewards ---
        ttk.Label(admin_right, text="Manage Rewards", font=("Arial", 12, "bold")).pack(anchor="w")
        self.admin_reward_list = tk.Listbox(admin_right, height=12, exportselection=False)
        self.admin_reward_list.pack(fill=tk.BOTH, expand=True, pady=5)

        admin_reward_btns = ttk.Frame(admin_right)
        admin_reward_btns.pack(anchor="w", pady=5)

        ttk.Button(admin_reward_btns, text="Add Reward",
                   command=self.open_add_reward_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(admin_reward_btns, text="Delete Reward",
                   command=self.delete_selected_reward).pack(side=tk.LEFT, padx=5)

    # ---------- Data Loading into UI ----------
    def load_customers(self):
        self.customers = self.service.get_customers()

        # Customer tab list
        self.customer_list.delete(0, tk.END)
        for c in self.customers:
            display = f"{c.name} ({c.email}) - {c.points} pts"
            self.customer_list.insert(tk.END, display)
        self.selected_customer_id = None
        self.customer_points_label.config(text="Points: -")

        # Admin tab customer list
        if hasattr(self, "admin_customer_list"):
            self.admin_customer_list.delete(0, tk.END)
            for c in self.customers:
                display = f"{c.name} ({c.email}) - {c.points} pts"
                self.admin_customer_list.insert(tk.END, display)

        # Employee tab customer list
        if hasattr(self, "emp_customer_list"):
            self.emp_customer_list.delete(0, tk.END)
            for c in self.customers:
                display = f"{c.name} - {c.points} pts"
                self.emp_customer_list.insert(tk.END, display)

    def load_rewards(self):
        self.rewards = self.service.get_rewards()

        # Customer tab reward list
        self.reward_list.delete(0, tk.END)
        for r in self.rewards:
            display = f"{r.name} - {r.cost} pts"
            self.reward_list.insert(tk.END, display)
        self.selected_reward_id = None
        self.reward_cost_label.config(text="Cost: -")

        # Admin tab reward list
        if hasattr(self, "admin_reward_list"):
            self.admin_reward_list.delete(0, tk.END)
            for r in self.rewards:
                display = f"{r.name} - {r.cost} pts"
                self.admin_reward_list.insert(tk.END, display)

    def load_pending_orders(self):
        self.pending_orders = self.service.get_pending_orders()
        if hasattr(self, "emp_order_list"):
            self.emp_order_list.delete(0, tk.END)
            for o in self.pending_orders:
                display = (
                    f"{o.customer_name} -> {o.reward_name} x{o.quantity} "
                    f"({o.points_spent} pts)"
                )
                self.emp_order_list.insert(tk.END, display)

    # ---------- Event Handlers (Customer Tab) ----------
    def on_customer_selected(self, event):
        idxs = self.customer_list.curselection()
        if not idxs:
            self.selected_customer_id = None
            self.customer_points_label.config(text="Points: -")
            return

        idx = idxs[0]
        customer = self.customers[idx]

        self.selected_customer_id = customer.id
        self.customer_points_label.config(text=f"Points: {customer.points}")

    def on_reward_selected(self, event):
        idxs = self.reward_list.curselection()
        if not idxs:
            self.selected_reward_id = None
            self.reward_cost_label.config(text="Cost: -")
            return

        idx = idxs[0]
        reward = self.rewards[idx]

        self.selected_reward_id = reward.id
        self.reward_cost_label.config(text=f"Cost: {reward.cost} pts")

    def redeem_click(self):
        # === Get currently selected customer from the listbox ===
        cust_idx = self.customer_list.curselection()
        if not cust_idx:
            messagebox.showwarning("Missing Selection", "Please select a customer.")
            return
        customer = self.customers[cust_idx[0]]
        customer_id = customer.id

        # === Get currently selected reward from the listbox ===
        reward_idx = self.reward_list.curselection()
        if not reward_idx:
            messagebox.showwarning("Missing Selection", "Please select a reward.")
            return
        reward = self.rewards[reward_idx[0]]
        reward_id = reward.id

        # === Validate quantity ===
        try:
            qty = int(self.qty_var.get())
        except ValueError:
            messagebox.showerror("Invalid Quantity", "Quantity must be a whole number.")
            return

        # === Call business logic ===
        try:
            updated_customer, reward_obj, total_cost = self.service.redeem_reward(
                customer_id=customer_id,
                reward_id=reward_id,
                quantity=qty
            )
        except ValueError as e:
            messagebox.showerror("Cannot Redeem", str(e))
            return

        # === Success message ===
        messagebox.showinfo(
            "Redeemed",
            f"{updated_customer.name} redeemed {qty} x {reward_obj.name}\n"
            f"Total cost: {total_cost} points\n"
            f"New balance: {updated_customer.points} points"
        )

        # === Refresh customers list + orders + reselect same customer ===
        self.load_customers()
        self.load_pending_orders()
        for i, c in enumerate(self.customers):
            if c.id == updated_customer.id:
                self.customer_list.selection_set(i)
                self.customer_list.see(i)
                self.customer_points_label.config(
                    text=f"Points: {updated_customer.points}"
                )
                break

    # ---------- Employee: Issue Points ----------
    def issue_points_click(self):
        idxs = self.emp_customer_list.curselection()
        if not idxs:
            messagebox.showwarning("No Selection", "Please select a customer.")
            return

        cust = self.customers[idxs[0]]

        try:
            points = int(self.emp_points_var.get().strip())
        except ValueError:
            messagebox.showerror("Invalid Input", "Points must be a whole number.")
            return

        if points <= 0:
            messagebox.showerror("Invalid Input", "Points must be greater than 0.")
            return

        if not messagebox.askyesno(
            "Confirm",
            f"Issue {points} points to {cust.name}?"
        ):
            return

        try:
            updated_customer = self.service.issue_points(cust.id, points)
        except Exception as e:
            messagebox.showerror("Error", f"Could not issue points: {e}")
            return

        messagebox.showinfo(
            "Success",
            f"Issued {points} points to {updated_customer.name}.\n"
            f"New balance: {updated_customer.points} points."
        )

        # Refresh customer lists so all tabs see updated points
        self.load_customers()

    # ---------- Employee: Process Orders ----------
    def fulfill_order_click(self):
        idxs = self.emp_order_list.curselection()
        if not idxs:
            messagebox.showwarning("No Selection", "Please select an order to fulfill.")
            return

        order = self.pending_orders[idxs[0]]

        if not messagebox.askyesno(
            "Confirm Fulfill",
            f"Fulfill order #{order.id} for {order.customer_name}: "
            f"{order.reward_name} x{order.quantity}?"
        ):
            return

        try:
            self.service.fulfill_order(order.id)
        except Exception as e:
            messagebox.showerror("Error", f"Could not fulfill order: {e}")
            return

        messagebox.showinfo("Fulfilled", f"Order #{order.id} has been fulfilled.")
        self.load_pending_orders()

    def cancel_order_click(self):
        idxs = self.emp_order_list.curselection()
        if not idxs:
            messagebox.showwarning("No Selection", "Please select an order to cancel.")
            return

        order = self.pending_orders[idxs[0]]

        if not messagebox.askyesno(
            "Confirm Cancel",
            f"Cancel order #{order.id} for {order.customer_name} "
            f"(refund {order.points_spent} points)?"
        ):
            return

        try:
            updated_customer = self.service.cancel_order(order.id)
        except Exception as e:
            messagebox.showerror("Error", f"Could not cancel order: {e}")
            return

        messagebox.showinfo(
            "Cancelled",
            f"Order #{order.id} has been cancelled.\n"
            f"{updated_customer.name}'s new balance: {updated_customer.points} points."
        )

        # Refresh both customers & orders
        self.load_customers()
        self.load_pending_orders()

    # ---------- Admin: Add/Delete Customers ----------
    def open_add_customer_dialog(self):
        win = tk.Toplevel(self.root)
        win.title("Add Customer")

        ttk.Label(win, text="Name:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        name_entry = ttk.Entry(win, width=30)
        name_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(win, text="Email:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        email_entry = ttk.Entry(win, width=30)
        email_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(win, text="Starting Points:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        points_entry = ttk.Entry(win, width=10)
        points_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        points_entry.insert(0, "0")

        def save():
            name = name_entry.get().strip()
            email = email_entry.get().strip()
            points_text = points_entry.get().strip()

            if not name:
                messagebox.showerror("Invalid Input", "Name is required.", parent=win)
                return
            if not email or "@" not in email:
                messagebox.showerror("Invalid Input", "Valid email is required.", parent=win)
                return
            try:
                points = int(points_text)
            except ValueError:
                messagebox.showerror("Invalid Input", "Points must be a whole number.", parent=win)
                return
            if points < 0:
                messagebox.showerror("Invalid Input", "Points cannot be negative.", parent=win)
                return

            try:
                self.service.add_customer(name, email, points)
            except Exception as e:
                messagebox.showerror("Error", f"Could not add customer: {e}", parent=win)
                return

            messagebox.showinfo("Success", "Customer added.", parent=win)
            self.load_customers()
            win.destroy()

        ttk.Button(win, text="Save", command=save).grid(row=3, column=0, padx=5, pady=10)
        ttk.Button(win, text="Cancel", command=win.destroy).grid(row=3, column=1, padx=5, pady=10)

    def delete_selected_customer(self):
        idxs = self.admin_customer_list.curselection()
        if not idxs:
            messagebox.showwarning("No Selection", "Please select a customer to delete.")
            return

        customer = self.customers[idxs[0]]
        if not messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete customer '{customer.name}'?",
        ):
            return

        try:
            self.service.delete_customer(customer.id)
        except Exception as e:
            messagebox.showerror("Error", f"Could not delete customer: {e}")
            return

        messagebox.showinfo("Deleted", "Customer deleted.")
        self.load_customers()

    # ---------- Admin: Add/Delete Rewards ----------
    def open_add_reward_dialog(self):
        win = tk.Toplevel(self.root)
        win.title("Add Reward")

        ttk.Label(win, text="Name:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        name_entry = ttk.Entry(win, width=30)
        name_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(win, text="Cost (points):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        cost_entry = ttk.Entry(win, width=10)
        cost_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        cost_entry.insert(0, "0")

        def save():
            name = name_entry.get().strip()
            cost_text = cost_entry.get().strip()

            if not name:
                messagebox.showerror("Invalid Input", "Name is required.", parent=win)
                return
            try:
                cost = int(cost_text)
            except ValueError:
                messagebox.showerror("Invalid Input", "Cost must be a whole number.", parent=win)
                return
            if cost <= 0:
                messagebox.showerror("Invalid Input", "Cost must be greater than 0.", parent=win)
                return

            try:
                self.service.add_reward(name, cost)
            except Exception as e:
                messagebox.showerror("Error", f"Could not add reward: {e}", parent=win)
                return

            messagebox.showinfo("Success", "Reward added.", parent=win)
            self.load_rewards()
            win.destroy()

        ttk.Button(win, text="Save", command=save).grid(row=2, column=0, padx=5, pady=10)
        ttk.Button(win, text="Cancel", command=win.destroy).grid(row=2, column=1, padx=5, pady=10)

    def delete_selected_reward(self):
        idxs = self.admin_reward_list.curselection()
        if not idxs:
            messagebox.showwarning("No Selection", "Please select a reward to delete.")
            return

        reward = self.rewards[idxs[0]]
        if not messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete reward '{reward.name}'?",
        ):
            return

        try:
            self.service.delete_reward(reward.id)
        except Exception as e:
            messagebox.showerror("Error", f"Could not delete reward: {e}")
            return

        messagebox.showinfo("Deleted", "Reward deleted.")
        self.load_rewards()


if __name__ == "__main__":
    # Initialize DB and launch app
    data_layer.init_db()

    root = tk.Tk()
    app = RewardShopApp(root)
    root.mainloop()
