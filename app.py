import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import customtkinter as ctk
import os

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def init_db():
    conn = sqlite3.connect("pos_system.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT,
            role TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT UNIQUE,
            name TEXT,
            cost_price REAL,
            price REAL,
            stock REAL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT,
            quantity REAL,
            cost_total REAL,
            total_price REAL,
            cashier_name TEXT,
            date_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS restock_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT,
            added_qty REAL,
            admin_name TEXT,
            date_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shop_name TEXT,
            address TEXT,
            phone TEXT,
            email TEXT
        )
    """)
    
    # Check if email column exists in older database files, if not add it
    cursor.execute("PRAGMA table_info(settings)")
    columns = [col[1] for col in cursor.fetchall()]
    if "email" not in columns:
        cursor.execute("ALTER TABLE settings ADD COLUMN email TEXT")
    
    cursor.execute("SELECT * FROM users WHERE username='admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('admin', '1234', 'Admin')")
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('cashier1', '1234', 'Cashier')")
        
    cursor.execute("SELECT COUNT(*) FROM settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO settings (shop_name, address, phone, email) VALUES ('MY SHOP NAME', 'Main Street, City', '077-0000000', 'info@myshop.com')")
        
    conn.commit()
    conn.close()

init_db()

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

class POSApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Commercial POS System")
        
        try:
            self.state("zoomed")
        except Exception:
            self.geometry("1280x850")
            
        self.lift()
        self.attributes('-topmost', True)
        self.after_idle(self.attributes, '-topmost', False)
            
        self.current_user = None
        self.current_role = None
        self.cart_items = []
        
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", font=("Arial", 11), rowheight=30, background="#ffffff", fieldbackground="#ffffff")
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"), background="#2C3E50", foreground="#ffffff")
        style.map("Treeview", background=[('selected', '#1ABC9C')])

        self.show_login_screen()

    def clear_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

    def show_login_screen(self):
        self.clear_screen()
        
        bg_frame = ctk.CTkFrame(self, fg_color="#EBF5FB", corner_radius=0)
        bg_frame.pack(fill=tk.BOTH, expand=True)
        
        card = ctk.CTkFrame(bg_frame, width=460, height=500, fg_color="#ffffff", corner_radius=20, border_width=1, border_color="#D5D8DC")
        card.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        header_frame = ctk.CTkFrame(card, height=90, fg_color="#2C3E50", corner_radius=15)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        header_frame.pack_propagate(False)
        
        brand_lbl = ctk.CTkLabel(header_frame, text="COMMERCIAL POS SYSTEM", font=("Arial", 18, "bold"), text_color="#ffffff")
        brand_lbl.pack(expand=True)
        
        form_container = ctk.CTkFrame(card, fg_color="transparent")
        form_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)
        
        sub_title = ctk.CTkLabel(form_container, text="Please sign in to continue", font=("Arial", 13), text_color="#7F8C8D")
        sub_title.pack(anchor="w", pady=(5, 12))
        
        tk.Label(form_container, text="Username", font=("Arial", 11, "bold"), bg="#ffffff", fg="#2C3E50").pack(anchor="w", pady=(0, 2))
        self.username_entry = ctk.CTkEntry(form_container, placeholder_text="Enter username", width=360, height=40, font=("Arial", 12))
        self.username_entry.pack(pady=(0, 12))
        
        tk.Label(form_container, text="Password", font=("Arial", 11, "bold"), bg="#ffffff", fg="#2C3E50").pack(anchor="w", pady=(0, 2))
        self.password_entry = ctk.CTkEntry(form_container, placeholder_text="Enter password", show="*", width=360, height=40, font=("Arial", 12))
        self.password_entry.pack(pady=(0, 15))
        self.password_entry.bind("<Return>", lambda e: self.verify_login())
        
        login_btn = ctk.CTkButton(form_container, text="Secure Login", command=self.verify_login, width=360, height=42, fg_color="#27AE60", hover_color="#219653", font=("Arial", 13, "bold"))
        login_btn.pack(pady=(0, 10))

        footer_lbl = ctk.CTkLabel(card, text="© 2026 All Rights Reserved | Developed By Haseli", font=("Arial", 10), text_color="#95A5A6")
        footer_lbl.pack(side=tk.BOTTOM, pady=12)

    def verify_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        conn = sqlite3.connect("pos_system.db")
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            self.current_user = username
            self.current_role = user[0]
            self.show_dashboard()
        else:
            messagebox.showerror("Authentication Error", "Invalid Username or Password")

    def show_dashboard(self):
        self.clear_screen()
        
        nav_frame = ctk.CTkFrame(self, height=65, corner_radius=0, fg_color="#2C3E50")
        nav_frame.pack(side=tk.TOP, fill=tk.X)
        
        lbl = ctk.CTkLabel(nav_frame, text=f"Dashboard  |  User: {self.current_user.upper()} ({self.current_role})", font=("Arial", 15, "bold"), text_color="#ffffff")
        lbl.pack(side=tk.LEFT, padx=25)
        
        logout_btn = ctk.CTkButton(nav_frame, text="Logout", fg_color="#E74C3C", hover_color="#C0392B", width=90, height=35, font=("Arial", 11, "bold"), command=self.show_login_screen)
        logout_btn.pack(side=tk.RIGHT, padx=25)
        
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
        self.tab_invoice = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_invoice, text="  Invoice (Billing)  ")
        self.setup_invoice_tab()
        
        self.tab_sales = ttk.Frame(self.notebook)
        sales_tab_title = "  Sales Reports & Profits  " if self.current_role == "Admin" else "  Sales History  "
        self.notebook.add(self.tab_sales, text=sales_tab_title)
        self.setup_sales_tab()
        
        if self.current_role == "Admin":
            self.tab_inventory = ttk.Frame(self.notebook)
            self.notebook.add(self.tab_inventory, text="  Stock & Inventory  ")
            self.setup_inventory_tab()
            
            self.tab_restock = ttk.Frame(self.notebook)
            self.notebook.add(self.tab_restock, text="  Restock History  ")
            self.setup_restock_history_tab()
            
            self.tab_settings = ttk.Frame(self.notebook)
            self.notebook.add(self.tab_settings, text="  Shop Settings  ")
            self.setup_settings_tab()
            
            self.tab_users = ttk.Frame(self.notebook)
            self.notebook.add(self.tab_users, text="  Manage Cashiers  ")
            self.setup_users_tab()

    def on_tab_changed(self, event):
        try:
            current_tab = self.notebook.index(self.notebook.select())
            current_tab_text = self.notebook.tab(current_tab, "text")
            if "Invoice" in current_tab_text:
                self.update_dropdown_values()
            elif "Stock" in current_tab_text and hasattr(self, 'stock_tree'):
                self.refresh_inventory_table()
            elif ("Sales" in current_tab_text or "History" in current_tab_text) and hasattr(self, 'sales_tree'):
                self.load_available_months()
                self.refresh_sales_table()
            elif "Restock History" in current_tab_text and hasattr(self, 'restock_tree'):
                self.refresh_restock_table()
            elif "Settings" in current_tab_text:
                self.load_shop_settings()
        except Exception:
            pass

    def setup_invoice_tab(self):
        frame = self.tab_invoice
        for widget in frame.winfo_children():
            widget.destroy()
        
        lbl = tk.Label(frame, text="Point of Sale - Fast Billing Counter", font=("Arial", 16, "bold"), fg="#2C3E50")
        lbl.pack(pady=12)
        
        input_frame = tk.LabelFrame(frame, text=" Product Selection & Barcode Scanning ", font=("Arial", 11, "bold"), padx=15, pady=12, bg="#F8F9F9")
        input_frame.pack(fill=tk.X, padx=25, pady=5)
        
        conn = sqlite3.connect("pos_system.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM products")
        products = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        tk.Label(input_frame, text="Item Name:", font=("Arial", 11, "bold"), bg="#F8F9F9").pack(side=tk.LEFT, padx=5)
        self.product_var = tk.StringVar(value=products[0] if products else "")
        self.prod_dropdown = ttk.Combobox(input_frame, textvariable=self.product_var, values=products, width=30, font=("Arial", 11))
        self.prod_dropdown.pack(side=tk.LEFT, padx=8)
        self.prod_dropdown.bind("<Button-1>", lambda e: self.update_dropdown_values())
        self.prod_dropdown.bind("<<ComboboxSelected>>", self.on_product_selected)
        
        tk.Label(input_frame, text="Barcode:", font=("Arial", 11, "bold"), bg="#F8F9F9").pack(side=tk.LEFT, padx=5)
        self.barcode_entry = ttk.Entry(input_frame, width=16, font=("Arial", 11))
        self.barcode_entry.pack(side=tk.LEFT, padx=8)
        self.barcode_entry.bind("<Return>", self.on_barcode_entered)
        
        tk.Label(input_frame, text="Quantity:", font=("Arial", 11, "bold"), bg="#F8F9F9").pack(side=tk.LEFT, padx=5)
        self.qty_entry = ttk.Entry(input_frame, width=10, font=("Arial", 11))
        self.qty_entry.pack(side=tk.LEFT, padx=8)
        
        add_to_cart_btn = tk.Button(input_frame, text="Add to Cart", bg="#2980B9", fg="white", font=("Arial", 11, "bold"), command=self.add_to_cart, width=14, height=1)
        add_to_cart_btn.pack(side=tk.LEFT, padx=15)

        self.sync_barcode_from_dropdown()

        self.cart_tree = ttk.Treeview(frame, columns=("Name", "Price", "Qty", "Total"), show="headings", height=12)
        self.cart_tree.heading("Name", text="Item Name")
        self.cart_tree.heading("Price", text="Unit Price (Rs)")
        self.cart_tree.heading("Qty", text="Quantity")
        self.cart_tree.heading("Total", text="Total (Rs)")
        
        self.cart_tree.column("Name", width=420, anchor=tk.W)
        self.cart_tree.column("Price", width=200, anchor=tk.CENTER)
        self.cart_tree.column("Qty", width=130, anchor=tk.CENTER)
        self.cart_tree.column("Total", width=250, anchor=tk.CENTER)
        
        self.cart_tree.pack(pady=10, padx=25, fill=tk.BOTH, expand=True)

        bottom_frame = tk.Frame(frame, bg="#F8F9F9", padx=15, pady=10)
        bottom_frame.pack(fill=tk.X, padx=25, pady=5)
        
        discount_frame = tk.Frame(bottom_frame, bg="#F8F9F9")
        discount_frame.pack(side=tk.LEFT, padx=5)
        
        tk.Label(discount_frame, text="Discount (Rs):", font=("Arial", 12, "bold"), bg="#F8F9F9").pack(side=tk.LEFT, padx=5)
        self.discount_entry = ttk.Entry(discount_frame, width=12, font=("Arial", 11))
        self.discount_entry.insert(0, "0.00")
        self.discount_entry.pack(side=tk.LEFT, padx=5)
        self.discount_entry.bind("<KeyRelease>", lambda e: self.refresh_cart_table())

        action_sub_frame = tk.Frame(frame, padx=10, pady=5)
        action_sub_frame.pack(fill=tk.X, padx=25, pady=10)
        
        self.grand_total_lbl = tk.Label(action_sub_frame, text="Grand Total: Rs. 0.00", font=("Arial", 16, "bold"), fg="#27AE60")
        self.grand_total_lbl.pack(side=tk.LEFT, padx=10)
        
        complete_btn = tk.Button(action_sub_frame, text="Complete Sale & Generate PDF Bill", bg="#27AE60", fg="white", font=("Arial", 12, "bold"), command=self.process_cart_sale, width=32, height=2)
        complete_btn.pack(side=tk.RIGHT, padx=10)
        
        clear_cart_btn = tk.Button(action_sub_frame, text="Clear Cart", bg="#C0392B", fg="white", font=("Arial", 11, "bold"), command=self.clear_cart, width=14, height=2)
        clear_cart_btn.pack(side=tk.RIGHT, padx=10)

    def update_dropdown_values(self):
        try:
            conn = sqlite3.connect("pos_system.db")
            cur = conn.cursor()
            cur.execute("SELECT name FROM products")
            updated_products = [row[0] for row in cur.fetchall()]
            conn.close()
            if hasattr(self, 'prod_dropdown'):
                self.prod_dropdown['values'] = updated_products
                if updated_products and not self.product_var.get():
                    self.product_var.set(updated_products[0])
        except Exception:
            pass

    def on_product_selected(self, event):
        self.sync_barcode_from_dropdown()

    def sync_barcode_from_dropdown(self):
        try:
            selected_name = self.product_var.get().strip()
            if not selected_name:
                return
            conn = sqlite3.connect("pos_system.db")
            cursor = conn.cursor()
            cursor.execute("SELECT barcode FROM products WHERE name=?", (selected_name,))
            res = cursor.fetchone()
            conn.close()
            if res and hasattr(self, 'barcode_entry'):
                self.barcode_entry.delete(0, tk.END)
                self.barcode_entry.insert(0, res[0])
        except Exception:
            pass

    def on_barcode_entered(self, event):
        barcode = self.barcode_entry.get().strip()
        if not barcode:
            return
            
        conn = sqlite3.connect("pos_system.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM products WHERE barcode=?", (barcode,))
        prod = cursor.fetchone()
        conn.close()
        
        if prod:
            self.product_var.set(prod[0])
            self.qty_entry.focus()
        else:
            messagebox.showerror("Error", f"Product with barcode '{barcode}' not found!")

    def add_to_cart(self):
        prod_name = self.product_var.get().strip()
        qty_str = self.qty_entry.get().strip()
        
        if not prod_name or not qty_str:
            messagebox.showerror("Error", "Please select a product and enter quantity!")
            return
            
        try:
            qty = float(qty_str)
            if qty <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid positive numeric quantity!")
            return
            
        conn = sqlite3.connect("pos_system.db")
        cursor = conn.cursor()
        cursor.execute("SELECT cost_price, price, stock FROM products WHERE name=?", (prod_name,))
        prod = cursor.fetchone()
        conn.close()
        
        if not prod:
            messagebox.showerror("Error", "Product not found!")
            return
            
        cost_price, price, current_stock = prod
        
        existing_cart_qty = 0
        for item in self.cart_items:
            if item[0] == prod_name:
                existing_cart_qty = item[3]
                break
                
        if (existing_cart_qty + qty) > current_stock:
            messagebox.showerror("Stock Error", f"Not enough stock! Available: {current_stock}")
            return
            
        total = price * qty
        cost_total = cost_price * qty
        
        found = False
        for i, item in enumerate(self.cart_items):
            if item[0] == prod_name:
                new_qty = item[3] + qty
                new_total = price * new_qty
                new_cost_total = cost_price * new_qty
                self.cart_items[i] = (prod_name, cost_price, price, new_qty, new_total, new_cost_total)
                found = True
                break
                
        if not found:
            self.cart_items.append((prod_name, cost_price, price, qty, total, cost_total))
            
        self.refresh_cart_table()
        self.qty_entry.delete(0, tk.END)

    def refresh_cart_table(self):
        if not hasattr(self, 'cart_tree'):
            return
            
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)
            
        sub_total = 0
        for item in self.cart_items:
            self.cart_tree.insert("", tk.END, values=(item[0], f"{item[2]:.2f}", item[3], f"{item[4]:.2f}"))
            sub_total += item[4]
            
        try:
            discount = float(self.discount_entry.get().strip() or 0.0)
        except ValueError:
            discount = 0.0
            
        grand_total = max(0.0, sub_total - discount)
        self.grand_total_lbl.config(text=f"Sub Total: Rs. {sub_total:,.2f} | Discount: Rs. {discount:,.2f} | Grand Total: Rs. {grand_total:,.2f}")

    def clear_cart(self):
        self.cart_items = []
        if hasattr(self, 'discount_entry'):
            self.discount_entry.delete(0, tk.END)
            self.discount_entry.insert(0, "0.00")
        self.refresh_cart_table()

    def process_cart_sale(self):
        if not self.cart_items:
            messagebox.showerror("Error", "Cart is empty!")
            return
            
        try:
            discount = float(self.discount_entry.get().strip() or 0.0)
        except ValueError:
            discount = 0.0
            
        sub_total = sum(item[4] for item in self.cart_items)
        grand_total = max(0.0, sub_total - discount)
        
        conn = sqlite3.connect("pos_system.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT datetime('now', 'localtime')")
        current_time = cursor.fetchone()[0]
        
        sale_items_data = []
        for item in self.cart_items:
            name, cost_price, price, qty, total, cost_total = item
            cursor.execute("UPDATE products SET stock = stock - ? WHERE name=?", (qty, name))
            cursor.execute("INSERT INTO sales (item_name, quantity, cost_total, total_price, cashier_name) VALUES (?, ?, ?, ?, ?)", 
                           (name, qty, cost_total, total, self.current_user))
            sale_items_data.append([name, f"{qty}", f"Rs. {price:,.2f}", f"Rs. {total:,.2f}"])
            
        conn.commit()
        sale_id = cursor.lastrowid
        conn.close()
        
        default_filename = f"INV_{sale_id:04d}.pdf"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=default_filename,
            filetypes=[("PDF Documents", "*.pdf"), ("All Files", "*.*")]
        )
        
        if file_path:
            try:
                self.generate_pdf_invoice(file_path, sale_id, current_time, sale_items_data, sub_total, discount, grand_total)
                messagebox.showinfo("Success", f"PDF Bill generated successfully and saved to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to generate PDF: {e}")
                
        self.clear_cart()

    def generate_pdf_invoice(self, file_path, sale_id, current_time, items_data, sub_total, discount, grand_total):
        conn = sqlite3.connect("pos_system.db")
        cursor = conn.cursor()
        cursor.execute("SELECT shop_name, address, phone, email FROM settings WHERE id=1")
        settings = cursor.fetchone()
        conn.close()
        
        shop_name = settings[0] if settings else "POS SHOP"
        shop_address = settings[1] if settings else "Address Line"
        shop_phone = settings[2] if settings else "000-0000000"
        shop_email = settings[3] if len(settings) > 3 and settings[3] else "info@shop.com"

        doc = SimpleDocTemplate(file_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        elements = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'TitleStyle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=16, alignment=1, textColor=colors.HexColor("#1a4314")
        )
        sub_style = ParagraphStyle(
            'SubStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=10, alignment=1, textColor=colors.HexColor("#555555")
        )
        bold_normal = ParagraphStyle(
            'BoldNormal', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10
        )
        
        elements.append(Paragraph(shop_name, title_style))
        elements.append(Paragraph(f"{shop_address}<br/>Hot Line: {shop_phone} | Email: {shop_email}", sub_style))
        elements.append(Spacer(1, 15))
        
        meta_data = [
            [Paragraph(f"<b>Bill No:</b> INV-{sale_id:04d}", styles['Normal']), Paragraph(f"<b>Date & Time:</b> {current_time}", styles['Normal'])],
            [Paragraph(f"<b>Cashier:</b> {self.current_user.upper()}", styles['Normal']), Paragraph("<b>Payment Mode:</b> Cash", styles['Normal'])]
        ]
        meta_table = Table(meta_data, colWidths=[250, 260])
        meta_table.setStyle(TableStyle([('BOTTOMPADDING', (0,0), (-1,-1), 6)]))
        elements.append(meta_table)
        elements.append(Spacer(1, 10))
        
        table_data = [["Item Description", "Qty", "Unit Price", "Total Price"]]
        for row in items_data:
            table_data.append([Paragraph(row[0], styles['Normal']), Paragraph(row[1], styles['Normal']), Paragraph(row[2], styles['Normal']), Paragraph(row[3], styles['Normal'])])
            
        table_data.append(["", "", Paragraph("Sub Total:", bold_normal), Paragraph(f"Rs. {sub_total:,.2f}", bold_normal)])
        table_data.append(["", "", Paragraph("Discount:", bold_normal), Paragraph(f"Rs. {discount:,.2f}", bold_normal)])
        table_data.append(["", "", Paragraph("Grand Total:", bold_normal), Paragraph(f"<b>Rs. {grand_total:,.2f}</b>", bold_normal)])
        
        item_table = Table(table_data, colWidths=[240, 60, 105, 105])
        item_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2C3E50")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (1,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('TOPPADDING', (0,0), (-1,0), 6),
            ('GRID', (0,0), (-1,-4), 0.5, colors.grey),
            ('BACKGROUND', (2,-3), (3,-1), colors.HexColor("#ECF0F1")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#2C3E50")),
        ]))
        elements.append(item_table)
        elements.append(Spacer(1, 20))
        
        footer_style = ParagraphStyle(
            'FooterStyle', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=9, alignment=1, textColor=colors.HexColor("#7F8C8D")
        )
        elements.append(Paragraph("Thank You For Your Business!<br/>Goods once sold are not exchangeable or returnable.", footer_style))
        
        doc.build(elements)

    def setup_inventory_tab(self):
        frame = self.tab_inventory
        for widget in frame.winfo_children():
            widget.destroy()
        
        lbl = tk.Label(frame, text="Stock & Inventory Management", font=("Arial", 16, "bold"), fg="#2C3E50")
        lbl.pack(pady=10)
        
        self.stock_tree = ttk.Treeview(frame, columns=("ID", "Barcode", "Name", "Cost", "Price", "Stock"), show="headings", height=11)
        self.stock_tree.heading("ID", text="ID")
        self.stock_tree.heading("Barcode", text="Barcode")
        self.stock_tree.heading("Name", text="Item Name")
        self.stock_tree.heading("Cost", text="Cost Price (Rs)")
        self.stock_tree.heading("Price", text="Selling Price (Rs)")
        self.stock_tree.heading("Stock", text="Available Qty")
        
        self.stock_tree.column("ID", width=45, anchor=tk.CENTER)
        self.stock_tree.column("Barcode", width=120, anchor=tk.CENTER)
        self.stock_tree.column("Name", width=300, anchor=tk.W)
        self.stock_tree.column("Cost", width=140, anchor=tk.CENTER)
        self.stock_tree.column("Price", width=140, anchor=tk.CENTER)
        self.stock_tree.column("Stock", width=130, anchor=tk.CENTER)
        
        self.stock_tree.pack(pady=10, padx=25, fill=tk.BOTH, expand=True)
        self.stock_tree.bind("<ButtonRelease-1>", self.select_item_from_stock)
        
        form_frame = tk.LabelFrame(frame, text=" Manage Inventory & Pricing ", font=("Arial", 11, "bold"), padx=20, pady=12, bg="#F8F9F9")
        form_frame.pack(fill=tk.X, padx=25, pady=5)
        
        input_sub_frame = tk.Frame(form_frame, bg="#F8F9F9")
        input_sub_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(input_sub_frame, text="Barcode:", font=("Arial", 10, "bold"), bg="#F8F9F9").pack(side=tk.LEFT, padx=3)
        self.new_barcode = ttk.Entry(input_sub_frame, width=12, font=("Arial", 11))
        self.new_barcode.pack(side=tk.LEFT, padx=6)
        
        tk.Label(input_sub_frame, text="Name:", font=("Arial", 10, "bold"), bg="#F8F9F9").pack(side=tk.LEFT, padx=3)
        self.new_name = ttk.Entry(input_sub_frame, width=22, font=("Arial", 11))
        self.new_name.pack(side=tk.LEFT, padx=6)
        
        tk.Label(input_sub_frame, text="Cost:", font=("Arial", 10, "bold"), bg="#F8F9F9").pack(side=tk.LEFT, padx=3)
        self.new_cost = ttk.Entry(input_sub_frame, width=10, font=("Arial", 11))
        self.new_cost.pack(side=tk.LEFT, padx=6)
        
        tk.Label(input_sub_frame, text="Price:", font=("Arial", 10, "bold"), bg="#F8F9F9").pack(side=tk.LEFT, padx=3)
        self.new_price = ttk.Entry(input_sub_frame, width=10, font=("Arial", 11))
        self.new_price.pack(side=tk.LEFT, padx=6)
        
        tk.Label(input_sub_frame, text="Stock:", font=("Arial", 10, "bold"), bg="#F8F9F9").pack(side=tk.LEFT, padx=3)
        self.new_stock = ttk.Entry(input_sub_frame, width=10, font=("Arial", 11))
        self.new_stock.pack(side=tk.LEFT, padx=6)
        
        btn_sub_frame = tk.Frame(form_frame, bg="#F8F9F9")
        btn_sub_frame.pack(fill=tk.X, pady=10)
        
        add_btn = tk.Button(btn_sub_frame, text="Add New Item", bg="#27AE60", fg="white", font=("Arial", 10, "bold"), command=self.add_new_product, width=16, height=1)
        add_btn.pack(side=tk.LEFT, padx=6)
        
        restock_btn = tk.Button(btn_sub_frame, text="Restock (+ Qty)", bg="#8E44AD", fg="white", font=("Arial", 10, "bold"), command=self.restock_product, width=16, height=1)
        restock_btn.pack(side=tk.LEFT, padx=6)
        
        update_btn = tk.Button(btn_sub_frame, text="Update/Edit", bg="#2980B9", fg="white", font=("Arial", 10, "bold"), command=self.update_product, width=16, height=1)
        update_btn.pack(side=tk.LEFT, padx=6)
        
        delete_btn = tk.Button(btn_sub_frame, text="Delete Item", bg="#C0392B", fg="white", font=("Arial", 10, "bold"), command=self.delete_product, width=16, height=1)
        delete_btn.pack(side=tk.LEFT, padx=6)

        self.refresh_inventory_table()

    def refresh_inventory_table(self):
        if hasattr(self, 'stock_tree'):
            for item in self.stock_tree.get_children():
                self.stock_tree.delete(item)
                
            conn = sqlite3.connect("pos_system.db")
            cursor = conn.cursor()
            cursor.execute("SELECT id, barcode, name, cost_price, price, stock FROM products")
            for row in cursor.fetchall():
                self.stock_tree.insert("", tk.END, values=row)
            conn.close()

    def select_item_from_stock(self, event):
        selected_item = self.stock_tree.selection()
        if selected_item:
            item_data = self.stock_tree.item(selected_item[0], "values")
            self.selected_id = item_data[0]
            
            self.new_barcode.delete(0, tk.END)
            self.new_barcode.insert(0, item_data[1])
            
            self.new_name.delete(0, tk.END)
            self.new_name.insert(0, item_data[2])
            
            self.new_cost.delete(0, tk.END)
            self.new_cost.insert(0, item_data[3])
            
            self.new_price.delete(0, tk.END)
            self.new_price.insert(0, item_data[4])
            
            self.new_stock.delete(0, tk.END)
            self.new_stock.insert(0, item_data[5])

    def add_new_product(self):
        barcode = self.new_barcode.get().strip()
        name = self.new_name.get().strip()
        cost = self.new_cost.get().strip()
        price = self.new_price.get().strip()
        stock = self.new_stock.get().strip()
        
        if not barcode or not name or not cost or not price or not stock:
            messagebox.showerror("Error", "All fields are required!")
            return
            
        try:
            c_val = float(cost)
            p_val = float(price)
            s_val = float(stock)
            if c_val < 0 or p_val < 0 or s_val < 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "Cost, Price and Stock must be valid positive numbers!")
            return
            
        conn = sqlite3.connect("pos_system.db")
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO products (barcode, name, cost_price, price, stock) VALUES (?, ?, ?, ?, ?)", (barcode, name, c_val, p_val, s_val))
            
            admin_name = self.current_user if self.current_user else "Admin"
            cursor.execute("INSERT INTO restock_history (item_name, added_qty, admin_name) VALUES (?, ?, ?)", 
                           (name, s_val, admin_name))
            
            conn.commit()
            messagebox.showinfo("Success", "New item added successfully and initial stock recorded!")
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", f"Barcode '{barcode}' already exists!")
        except Exception as e:
            messagebox.showerror("Error", f"Database Error: {e}")
        finally:
            conn.close()
            
        self.clear_form()
        self.refresh_inventory_table()
        self.update_dropdown_values()
        if hasattr(self, 'restock_tree'):
            self.refresh_restock_table()

    def restock_product(self):
        if not hasattr(self, 'selected_id') or not self.selected_id:
            messagebox.showerror("Error", "Please select an item from the table to restock!")
            return
            
        stock_str = self.new_stock.get().strip()
        if not stock_str:
            messagebox.showerror("Error", "Please enter the quantity to add in the Stock box!")
            return
            
        try:
            add_qty = float(stock_str)
            if add_qty <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "Restock quantity must be a valid positive number!")
            return
            
        conn = sqlite3.connect("pos_system.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name, stock FROM products WHERE id=?", (self.selected_id,))
        res = cursor.fetchone()
        
        if res:
            item_name, current_stock = res
            new_stock = current_stock + add_qty
            cursor.execute("UPDATE products SET stock=? WHERE id=?", (new_stock, self.selected_id))
            
            admin_name = self.current_user if self.current_user else "Admin"
            cursor.execute("INSERT INTO restock_history (item_name, added_qty, admin_name) VALUES (?, ?, ?)", 
                           (item_name, add_qty, admin_name))
            conn.commit()
            messagebox.showinfo("Success", f"Successfully added {add_qty} to stock! New Total Stock: {new_stock}")
            
        conn.close()
        self.clear_form()
        self.refresh_inventory_table()
        if hasattr(self, 'restock_tree'):
            self.refresh_restock_table()

    def update_product(self):
        if not hasattr(self, 'selected_id') or not self.selected_id:
            messagebox.showerror("Error", "Please select an item from the table to update!")
            return
            
        barcode = self.new_barcode.get().strip()
        name = self.new_name.get().strip()
        cost = self.new_cost.get().strip()
        price = self.new_price.get().strip()
        stock = self.new_stock.get().strip()
        
        if not barcode or not name or not cost or not price or not stock:
            messagebox.showerror("Error", "All fields are required!")
            return
            
        try:
            c_val = float(cost)
            p_val = float(price)
            s_val = float(stock)
            if c_val < 0 or p_val < 0 or s_val < 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "Cost, Price and Stock must be valid positive numbers!")
            return
            
        conn = sqlite3.connect("pos_system.db")
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE products SET barcode=?, name=?, cost_price=?, price=?, stock=? WHERE id=?", (barcode, name, c_val, p_val, s_val, self.selected_id))
            conn.commit()
            messagebox.showinfo("Success", "Inventory item updated successfully!")
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", f"Barcode '{barcode}' already exists for another item!")
        except Exception as e:
            messagebox.showerror("Error", f"Database Error: {e}")
        finally:
            conn.close()
            
        self.clear_form()
        self.refresh_inventory_table()
        self.update_dropdown_values()

    def delete_product(self):
        if not hasattr(self, 'selected_id') or not self.selected_id:
            messagebox.showerror("Error", "Please select an item from the table to delete!")
            return
            
        conn = sqlite3.connect("pos_system.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE id=?", (self.selected_id,))
        conn.commit()
        conn.close()
        
        messagebox.showinfo("Success", "Item removed from inventory successfully!")
        self.clear_form()
        self.refresh_inventory_table()
        self.update_dropdown_values()

    def clear_form(self):
        self.selected_id = None
        self.new_barcode.delete(0, tk.END)
        self.new_name.delete(0, tk.END)
        self.new_cost.delete(0, tk.END)
        self.new_price.delete(0, tk.END)
        self.new_stock.delete(0, tk.END)

    def setup_restock_history_tab(self):
        frame = self.tab_restock
        for widget in frame.winfo_children():
            widget.destroy()
            
        lbl = tk.Label(frame, text="Stock Restock History Log", font=("Arial", 16, "bold"), fg="#2C3E50")
        lbl.pack(pady=12)
        
        self.restock_tree = ttk.Treeview(frame, columns=("ID", "Item Name", "Added Qty", "Admin", "Date & Time"), show="headings", height=14)
        self.restock_tree.heading("ID", text="ID")
        self.restock_tree.heading("Item Name", text="Item Name")
        self.restock_tree.heading("Added Qty", text="Added Quantity")
        self.restock_tree.heading("Admin", text="Restocked By")
        self.restock_tree.heading("Date & Time", text="Date & Time")
        
        self.restock_tree.column("ID", width=60, anchor=tk.CENTER)
        self.restock_tree.column("Item Name", width=300, anchor=tk.W)
        self.restock_tree.column("Added Qty", width=160, anchor=tk.CENTER)
        self.restock_tree.column("Admin", width=190, anchor=tk.CENTER)
        self.restock_tree.column("Date & Time", width=250, anchor=tk.CENTER)
        
        self.restock_tree.pack(pady=10, padx=25, fill=tk.BOTH, expand=True)
        self.refresh_restock_table()

    def refresh_restock_table(self):
        if not hasattr(self, 'restock_tree'):
            return
        for item in self.restock_tree.get_children():
            self.restock_tree.delete(item)
            
        conn = sqlite3.connect("pos_system.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, item_name, added_qty, admin_name, date_time FROM restock_history ORDER BY date_time DESC")
        for row in cursor.fetchall():
            self.restock_tree.insert("", tk.END, values=row)
        conn.close()

    def setup_settings_tab(self):
        frame = self.tab_settings
        for widget in frame.winfo_children():
            widget.destroy()
            
        lbl = tk.Label(frame, text="Shop Settings & Invoice Header Information", font=("Arial", 16, "bold"), fg="#2C3E50")
        lbl.pack(pady=20)
        
        form_frame = tk.Frame(frame, bg="#F8F9F9", padx=30, pady=20)
        form_frame.pack(pady=10)
        
        tk.Label(form_frame, text="Shop Name:", font=("Arial", 12, "bold"), bg="#F8F9F9").grid(row=0, column=0, sticky="w", pady=10)
        self.shop_name_entry = ttk.Entry(form_frame, width=40, font=("Arial", 12))
        self.shop_name_entry.grid(row=0, column=1, padx=15, pady=10)
        
        tk.Label(form_frame, text="Shop Address:", font=("Arial", 12, "bold"), bg="#F8F9F9").grid(row=1, column=0, sticky="w", pady=10)
        self.shop_address_entry = ttk.Entry(form_frame, width=40, font=("Arial", 12))
        self.shop_address_entry.grid(row=1, column=1, padx=15, pady=10)
        
        tk.Label(form_frame, text="Phone / Hotline:", font=("Arial", 12, "bold"), bg="#F8F9F9").grid(row=2, column=0, sticky="w", pady=10)
        self.shop_phone_entry = ttk.Entry(form_frame, width=40, font=("Arial", 12))
        self.shop_phone_entry.grid(row=2, column=1, padx=15, pady=10)
        
        tk.Label(form_frame, text="Email Address:", font=("Arial", 12, "bold"), bg="#F8F9F9").grid(row=3, column=0, sticky="w", pady=10)
        self.shop_email_entry = ttk.Entry(form_frame, width=40, font=("Arial", 12))
        self.shop_email_entry.grid(row=3, column=1, padx=15, pady=10)
        
        save_btn = tk.Button(frame, text="Save Shop Settings", bg="#27AE60", fg="white", font=("Arial", 12, "bold"), command=self.save_shop_settings, width=28, height=2)
        save_btn.pack(pady=20)
        
        self.load_shop_settings()

    def load_shop_settings(self):
        try:
            conn = sqlite3.connect("pos_system.db")
            cursor = conn.cursor()
            cursor.execute("SELECT shop_name, address, phone, email FROM settings WHERE id=1")
            res = cursor.fetchone()
            conn.close()
            
            if res and hasattr(self, 'shop_name_entry'):
                self.shop_name_entry.delete(0, tk.END)
                self.shop_name_entry.insert(0, res[0])
                self.shop_address_entry.delete(0, tk.END)
                self.shop_address_entry.insert(0, res[1])
                self.shop_phone_entry.delete(0, tk.END)
                self.shop_phone_entry.insert(0, res[2])
                if hasattr(self, 'shop_email_entry'):
                    self.shop_email_entry.delete(0, tk.END)
                    self.shop_email_entry.insert(0, res[3] if res[3] else "")
        except Exception:
            pass

    def save_shop_settings(self):
        name = self.shop_name_entry.get().strip()
        address = self.shop_address_entry.get().strip()
        phone = self.shop_phone_entry.get().strip()
        email = self.shop_email_entry.get().strip()
        
        if not name or not address or not phone:
            messagebox.showerror("Error", "Shop Name, Address and Phone are required!")
            return
            
        conn = sqlite3.connect("pos_system.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE settings SET shop_name=?, address=?, phone=?, email=? WHERE id=1", (name, address, phone, email))
        conn.commit()
        conn.close()
        
        messagebox.showinfo("Success", "Shop settings and email updated successfully!")

    def setup_sales_tab(self):
        frame = self.tab_sales
        for widget in frame.winfo_children():
            widget.destroy()
            
        is_admin = (self.current_role == "Admin")
        
        title_text = "Sales History, Monthly Revenue & Profit Reports" if is_admin else "Sales History Records"
        lbl = tk.Label(frame, text=title_text, font=("Arial", 16, "bold"), fg="#2C3E50")
        lbl.pack(pady=10)
        
        filter_frame = tk.Frame(frame, bg="#F8F9F9", padx=15, pady=8)
        filter_frame.pack(fill=tk.X, padx=25, pady=5)
        
        tk.Label(filter_frame, text="Select Month (YYYY-MM):", font=("Arial", 11, "bold"), bg="#F8F9F9").pack(side=tk.LEFT, padx=8)
        
        self.month_var = tk.StringVar(value="All Months")
        self.month_dropdown = ttk.Combobox(filter_frame, textvariable=self.month_var, values=["All Months"], width=18, font=("Arial", 11))
        self.month_dropdown.pack(side=tk.LEFT, padx=8)
        
        filter_btn = tk.Button(filter_frame, text="Filter Report", bg="#2980B9", fg="white", font=("Arial", 10, "bold"), command=self.refresh_sales_table, width=16)
        filter_btn.pack(side=tk.LEFT, padx=12)
        
        reset_btn = tk.Button(filter_frame, text="Show All", bg="#7F8C8D", fg="white", font=("Arial", 10, "bold"), command=self.reset_sales_filter, width=12)
        reset_btn.pack(side=tk.LEFT, padx=8)

        if is_admin:
            cols = ("Sale ID", "Item", "Qty", "Total", "Profit", "Cashier", "Time")
        else:
            cols = ("Sale ID", "Item", "Qty", "Total", "Cashier", "Time")
            
        self.sales_tree = ttk.Treeview(frame, columns=cols, show="headings", height=11)
        self.sales_tree.heading("Sale ID", text="ID")
        self.sales_tree.heading("Item", text="Item Name")
        self.sales_tree.heading("Qty", text="Quantity")
        self.sales_tree.heading("Total", text="Total (Rs)")
        if is_admin:
            self.sales_tree.heading("Profit", text="Profit (Rs)")
        self.sales_tree.heading("Cashier", text="Cashier")
        self.sales_tree.heading("Time", text="Date & Time")
        
        self.sales_tree.column("Sale ID", width=50, anchor=tk.CENTER)
        self.sales_tree.column("Item", width=280 if not is_admin else 240, anchor=tk.W)
        self.sales_tree.column("Qty", width=90 if not is_admin else 80, anchor=tk.CENTER)
        self.sales_tree.column("Total", width=150 if not is_admin else 130, anchor=tk.CENTER)
        if is_admin:
            self.sales_tree.column("Profit", width=130, anchor=tk.CENTER)
        self.sales_tree.column("Cashier", width=140 if not is_admin else 120, anchor=tk.CENTER)
        self.sales_tree.column("Time", width=200 if not is_admin else 170, anchor=tk.CENTER)
        
        self.sales_tree.pack(pady=8, padx=25, fill=tk.BOTH, expand=True)
        
        pdf_btn_text = "Download Monthly & Profit Report (PDF)" if is_admin else "Download Monthly Sales Report (PDF)"
        pdf_btn = tk.Button(frame, text=pdf_btn_text, bg="#1B4F72", fg="white", font=("Arial", 11, "bold"), command=self.download_sales_pdf, width=40, height=2)
        pdf_btn.pack(pady=10)
        
        self.load_available_months()
        self.refresh_sales_table()

    def load_available_months(self):
        try:
            conn = sqlite3.connect("pos_system.db")
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT strftime('%Y-%m', date_time) FROM sales ORDER BY date_time DESC")
            months = [row[0] for row in cursor.fetchall() if row[0]]
            conn.close()
            
            if hasattr(self, 'month_dropdown'):
                self.month_dropdown['values'] = ["All Months"] + months
        except Exception:
            pass

    def reset_sales_filter(self):
        if hasattr(self, 'month_var'):
            self.month_var.set("All Months")
        self.refresh_sales_table()

    def refresh_sales_table(self):
        if not hasattr(self, 'sales_tree'):
            return
            
        for item in self.sales_tree.get_children():
            self.sales_tree.delete(item)
            
        selected_month = self.month_var.get() if hasattr(self, 'month_var') else "All Months"
        is_admin = (self.current_role == "Admin")
        
        conn = sqlite3.connect("pos_system.db")
        cursor = conn.cursor()
        
        if selected_month and selected_month != "All Months":
            cursor.execute("SELECT sale_id, item_name, quantity, cost_total, total_price, cashier_name, date_time FROM sales WHERE strftime('%Y-%m', date_time) = ?", (selected_month,))
        else:
            cursor.execute("SELECT sale_id, item_name, quantity, cost_total, total_price, cashier_name, date_time FROM sales")
            
        for row in cursor.fetchall():
            sale_id, item_name, qty, cost_total, total_price, cashier, dt = row
            if is_admin:
                profit = total_price - cost_total
                self.sales_tree.insert("", tk.END, values=(sale_id, item_name, qty, f"{total_price:,.2f}", f"{profit:,.2f}", cashier, dt))
            else:
                self.sales_tree.insert("", tk.END, values=(sale_id, item_name, qty, f"{total_price:,.2f}", cashier, dt))
        conn.close()

    def download_sales_pdf(self):
        selected_month = self.month_var.get() if hasattr(self, 'month_var') else "All Months"
        is_admin = (self.current_role == "Admin")
        file_suffix = f"_{selected_month}" if selected_month != "All Months" else "_All_Time"
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=f"Sales_Report{file_suffix}.pdf",
            filetypes=[("PDF Documents", "*.pdf"), ("All Files", "*.*")]
        )
        if not file_path:
            return
            
        try:
            conn = sqlite3.connect("pos_system.db")
            cursor = conn.cursor()
            cursor.execute("SELECT shop_name, address, phone FROM settings WHERE id=1")
            set_res = cursor.fetchone()
            shop_name = set_res[0] if set_res else "POS SHOP"
            
            if selected_month and selected_month != "All Months":
                cursor.execute("SELECT sale_id, item_name, quantity, cost_total, total_price, cashier_name, date_time FROM sales WHERE strftime('%Y-%m', date_time) = ?", (selected_month,))
                report_subtitle = f"Monthly Sales Report ({selected_month})"
            else:
                cursor.execute("SELECT sale_id, item_name, quantity, cost_total, total_price, cashier_name, date_time FROM sales")
                report_subtitle = "Complete Official Sales Report (All Time)"
                
            rows = cursor.fetchall()
            conn.close()
            
            doc = SimpleDocTemplate(file_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
            elements = []
            
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'TitleStyle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=16, alignment=1, textColor=colors.HexColor("#1a4314")
            )
            sub_style = ParagraphStyle(
                'SubStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=10, alignment=1, textColor=colors.HexColor("#555555")
            )
            
            elements.append(Paragraph(shop_name, title_style))
            elements.append(Paragraph(report_subtitle, sub_style))
            elements.append(Spacer(1, 15))
            
            if is_admin:
                table_data = [["ID", "Item Name", "Qty", "Total (Rs)", "Profit (Rs)", "Cashier", "Date & Time"]]
            else:
                table_data = [["ID", "Item Name", "Qty", "Total (Rs)", "Cashier", "Date & Time"]]
                
            total_revenue = 0
            total_profit = 0
            
            for r in rows:
                rev = r[4]
                prof = r[4] - r[3]
                total_revenue += rev
                total_profit += prof
                if is_admin:
                    table_data.append([str(r[0]), r[1], str(r[2]), f"{rev:,.2f}", f"{prof:,.2f}", r[5], r[6]])
                else:
                    table_data.append([str(r[0]), r[1], str(r[2]), f"{rev:,.2f}", r[5], r[6]])
                
            if is_admin:
                sales_table = Table(table_data, colWidths=[35, 160, 50, 95, 95, 75, 120])
            else:
                sales_table = Table(table_data, colWidths=[40, 190, 60, 100, 90, 130])
                
            sales_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2C3E50")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('ALIGN', (1,0), (1,-1), 'LEFT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ]))
            elements.append(sales_table)
            elements.append(Spacer(1, 15))
            
            bold_style = ParagraphStyle('Bold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, textColor=colors.HexColor("#1a4314"))
            elements.append(Paragraph(f"<b>Total Revenue for Selected Period: Rs. {total_revenue:,.2f}</b>", bold_style))
            if is_admin:
                elements.append(Spacer(1, 5))
                elements.append(Paragraph(f"<b>Total Net Profit for Selected Period: Rs. {total_profit:,.2f}</b>", bold_style))
            
            doc.build(elements)
            messagebox.showinfo("Success", f"Sales Report PDF successfully saved to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate Sales Report PDF: {e}")

    def setup_users_tab(self):
        frame = self.tab_users
        for widget in frame.winfo_children():
            widget.destroy()
        
        lbl = tk.Label(frame, text="Create New Cashier Account", font=("Arial", 16, "bold"), fg="#2C3E50")
        lbl.pack(pady=20)
        
        form_frame = tk.Frame(frame, bg="#F8F9F9", padx=30, pady=25)
        form_frame.pack(pady=10)
        
        tk.Label(form_frame, text="Username:", font=("Arial", 12, "bold"), bg="#F8F9F9").grid(row=0, column=0, sticky="w", pady=12)
        self.c_user = ttk.Entry(form_frame, width=30, font=("Arial", 12))
        self.c_user.grid(row=0, column=1, padx=15, pady=12)
        
        tk.Label(form_frame, text="Password:", font=("Arial", 12, "bold"), bg="#F8F9F9").grid(row=1, column=0, sticky="w", pady=12)
        self.c_pass = ttk.Entry(form_frame, width=30, show="*", font=("Arial", 12))
        self.c_pass.grid(row=1, column=1, padx=15, pady=12)
        
        add_user_btn = tk.Button(frame, text="Create Cashier Account", bg="#27AE60", fg="white", font=("Arial", 12, "bold"), command=self.add_user, width=28, height=2)
        add_user_btn.pack(pady=20)

    def add_user(self):
        username = self.c_user.get().strip()
        password = self.c_pass.get().strip()
        
        if not username or not password:
            messagebox.showerror("Error", "Username and Password required!")
            return
            
        conn = sqlite3.connect("pos_system.db")
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, 'Cashier')", (username, password))
            conn.commit()
            messagebox.showinfo("Success", f"Cashier account '{username}' created successfully!")
            self.c_user.delete(0, tk.END)
            self.c_pass.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"Error: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    app = POSApp()
    app.mainloop()