import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from src.database import DatabaseManager
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class OrdersFrame(ctk.CTkFrame):
    def __init__(self, master, db: DatabaseManager):
        super().__init__(master)
        self.db = db
        self.is_destroyed = False
        
        self.label = ctk.CTkLabel(self, text="Aktif Siparişler", font=("Arial", 20, "bold"))
        self.label.pack(pady=10)
        
        # Treeview for Orders
        self.tree_frame = ctk.CTkFrame(self)
        self.tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Style configuration
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", 
                        background="#2a2d2e",
                        foreground="white",
                        rowheight=35,
                        fieldbackground="#343638",
                        font=("Arial", 12))
        style.configure("Treeview.Heading", font=("Arial", 13, "bold"))
        style.map("Treeview", background=[('selected', '#1f538d')])

        columns = ("id", "customer", "phone", "delivery", "total", "status", "date")
        self.tree = ttk.Treeview(self.tree_frame, columns=columns, show="headings", height=15)
        
        self.tree.heading("id", text="ID")
        self.tree.heading("customer", text="Müşteri")
        self.tree.heading("phone", text="Telefon")
        self.tree.heading("delivery", text="Teslimat")
        self.tree.heading("total", text="Tutar")
        self.tree.heading("status", text="Durum")
        self.tree.heading("date", text="Tarih")
        
        self.tree.column("id", width=40, anchor="center")
        self.tree.column("total", width=100, anchor="center")
        self.tree.column("status", width=100, anchor="center")
        
        self.tree.tag_configure("pending", background="#8B0000", foreground="white") # Dark Red
        self.tree.tag_configure("paid", background="#006400", foreground="white") # Dark Green
        
        self.tree.pack(side="left", fill="both", expand=True)
        
        # Buttons
        self.btn_frame = ctk.CTkFrame(self)
        self.btn_frame.pack(fill="x", padx=10, pady=10)
        
        self.btn_details = ctk.CTkButton(self.btn_frame, text="Sipariş Detayı", command=self.show_details)
        self.btn_details.pack(side="left", padx=5)
        
        self.btn_approve = ctk.CTkButton(self.btn_frame, text="Ödemeyi Onayla", command=self.approve_payment, fg_color="green")
        self.btn_approve.pack(side="left", padx=5)
        
        self.btn_deliver = ctk.CTkButton(self.btn_frame, text="Teslim Edildi", command=self.mark_delivered, fg_color="#D35B58") # Red-ish
        self.btn_deliver.pack(side="left", padx=5)
        
        self.btn_refresh = ctk.CTkButton(self.btn_frame, text="Yenile", command=self.refresh_data)
        self.btn_refresh.pack(side="right", padx=5)
        
        self.refresh_data()
        self.auto_refresh()

    def destroy(self):
        self.is_destroyed = True
        super().destroy()

    def auto_refresh(self):
        if self.is_destroyed:
            return
        
        if not self.tree.selection():
            self.refresh_data()
            
        self.after(5000, self.auto_refresh)

    def refresh_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        orders = self.db.get_orders()
        for order in orders:
            if order['status'] in ['Pending', 'Paid']:
                tag = "pending" if order['status'] == "Pending" else "paid"
                # Show discounted total if any
                total_disp = f"{order['total_price']} TL"
                self.tree.insert("", "end", values=(
                    order['id'], order['customer_name'], order['phone'], 
                    order['delivery_method'], total_disp, 
                    order['status'], order['created_at']
                ), tags=(tag,))

    def get_selected_id(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen bir sipariş seçin.")
            return None
        return self.tree.item(selected[0])['values'][0]

    def show_details(self):
        oid = self.get_selected_id()
        if not oid: return
        
        all_orders = self.db.get_orders()
        order = next((o for o in all_orders if o['id'] == oid), None)
        
        if order:
            items_str = "\n".join([f"{i['quantity']}x {i['product_name']} ({i['price']} TL)" for i in order['items']])
            details = (
                f"ID: {order['id']}\n"
                f"Müşteri: {order['customer_name']}\n"
                f"Not: {order['note']}\n\n"
                f"--- Ürünler ---\n{items_str}\n\n"
                f"Toplam: {order['total_price']} TL"
            )
            if order.get('coupon_code'):
                details += f"\n🎟️ Kupon: {order['coupon_code']} (-{order['discount_amount']} TL)"
                
            messagebox.showinfo("Sipariş Detayı", details)

    def approve_payment(self):
        oid = self.get_selected_id()
        if oid:
            self.db.update_order_status(oid, "Paid")
            self.refresh_data()

    def mark_delivered(self):
        oid = self.get_selected_id()
        if oid:
            self.db.update_order_status(oid, "Delivered")
            self.refresh_data()

class ProductsFrame(ctk.CTkFrame):
    def __init__(self, master, db: DatabaseManager):
        super().__init__(master)
        self.db = db
        self.is_destroyed = False
        
        self.label = ctk.CTkLabel(self, text="Ürün Yönetimi", font=("Arial", 20, "bold"))
        self.label.pack(pady=10)
        
        # Controls Frame
        self.ctrl_frame = ctk.CTkFrame(self)
        self.ctrl_frame.pack(fill="x", padx=10, pady=5)
        
        self.cat_var = ctk.StringVar(value="Kahve")
        self.seg_button = ctk.CTkSegmentedButton(self.ctrl_frame, values=["Kahve", "Kuru Meyve"], variable=self.cat_var, command=self.load_products)
        self.seg_button.pack(side="left", padx=10)
        
        self.btn_add = ctk.CTkButton(self.ctrl_frame, text="+ Yeni Ürün Ekle", command=self.open_add_popup, fg_color="green")
        self.btn_add.pack(side="right", padx=10)
        
        # Scrollable Frame for products
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.product_widgets = []
        self.load_products("Kahve")
        self.auto_refresh()

    def destroy(self):
        self.is_destroyed = True
        super().destroy()

    def auto_refresh(self):
        if self.is_destroyed:
            return
        
        focused_widget = self.focus_get()
        if isinstance(focused_widget, ctk.CTkEntry) and str(focused_widget).startswith(str(self)):
            pass
        else:
            try:
               self.load_products(self.cat_var.get())
            except Exception:
               pass
           
        self.after(3000, self.auto_refresh)
        
    def load_products(self, category):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.product_widgets = []
        
        products = self.db.get_products_by_category(category)
        
        h_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        h_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(h_frame, text="Ürün Adı", width=200, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(h_frame, text="Fiyat", width=80).pack(side="left", padx=5)
        ctk.CTkLabel(h_frame, text="Stok", width=80).pack(side="left", padx=5)
        ctk.CTkLabel(h_frame, text="Aktif", width=50).pack(side="left", padx=5)
        
        for p in products:
            row = ctk.CTkFrame(self.scroll_frame)
            row.pack(fill="x", pady=2)
            
            ent_name = ctk.CTkEntry(row, width=200)
            ent_name.insert(0, p['name'])
            ent_name.pack(side="left", padx=5)
            
            ent_price = ctk.CTkEntry(row, width=80)
            ent_price.insert(0, str(p['price']))
            ent_price.pack(side="left", padx=5)
            
            ent_stock = ctk.CTkEntry(row, width=80)
            ent_stock.insert(0, str(p['stock']))
            ent_stock.pack(side="left", padx=5)
            
            chk_active = ctk.CTkCheckBox(row, text="", width=50)
            if p['is_active']: chk_active.select()
            chk_active.pack(side="left", padx=5)
            
            btn_save = ctk.CTkButton(row, text="Kaydet", width=60, 
                                     command=lambda pid=p['id'], en=ent_name, ep=ent_price, es=ent_stock, ca=chk_active: self.save_product(pid, en, ep, es, ca))
            btn_save.pack(side="left", padx=10)
            
    def save_product(self, pid, ent_name, ent_price, ent_stock, chk_active):
        try:
            name = ent_name.get()
            price = float(ent_price.get())
            stock = int(ent_stock.get())
            is_active = chk_active.get()
            self.db.update_product(pid, name, price, stock, is_active)
            messagebox.showinfo("Başarılı", "Ürün güncellendi.")
        except ValueError:
            messagebox.showerror("Hata", "Lütfen geçerli sayı girin.")

    def open_add_popup(self):
        top = ctk.CTkToplevel(self)
        top.title("Yeni Ürün Ekle")
        top.geometry("300x300")
        
        ctk.CTkLabel(top, text="Kategori:").pack(pady=5)
        cat_var = ctk.StringVar(value="Kahve")
        ctk.CTkOptionMenu(top, variable=cat_var, values=["Kahve", "Kuru Meyve"]).pack(pady=5)
        
        ctk.CTkLabel(top, text="Ürün Adı:").pack(pady=5)
        ent_name = ctk.CTkEntry(top)
        ent_name.pack(pady=5)
        
        ctk.CTkLabel(top, text="Fiyat:").pack(pady=5)
        ent_price = ctk.CTkEntry(top)
        ent_price.pack(pady=5)
        
        ctk.CTkLabel(top, text="Stok:").pack(pady=5)
        ent_stock = ctk.CTkEntry(top)
        ent_stock.pack(pady=5)
        
        def add():
            try:
                name = ent_name.get()
                price = float(ent_price.get())
                stock = int(ent_stock.get())
                category = cat_var.get()
                if not name:
                    messagebox.showerror("Hata", "İsim boş olamaz.")
                    return
                self.db.add_product(category, name, price, stock)
                messagebox.showinfo("Başarılı", "Ürün eklendi.")
                self.load_products(self.cat_var.get())
                top.destroy()
            except ValueError:
                messagebox.showerror("Hata", "Fiyat/Stok sayı olmalı.")
                
        ctk.CTkButton(top, text="Ekle", command=add).pack(pady=20)

class CouponsFrame(ctk.CTkFrame):
    def __init__(self, master, db: DatabaseManager):
        super().__init__(master)
        self.db = db
        
        self.label = ctk.CTkLabel(self, text="İndirim Kuponları", font=("Arial", 20, "bold"))
        self.label.pack(pady=10)
        
        # New Coupon
        self.add_frame = ctk.CTkFrame(self)
        self.add_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(self.add_frame, text="Kod:").pack(side="left", padx=5)
        self.ent_code = ctk.CTkEntry(self.add_frame, width=100)
        self.ent_code.pack(side="left", padx=5)
        
        ctk.CTkLabel(self.add_frame, text="İndirim (%):").pack(side="left", padx=5)
        self.ent_percent = ctk.CTkEntry(self.add_frame, width=50)
        self.ent_percent.pack(side="left", padx=5)
        
        ctk.CTkLabel(self.add_frame, text="Limit (0=Sınırsız):").pack(side="left", padx=5)
        self.ent_limit = ctk.CTkEntry(self.add_frame, width=50)
        self.ent_limit.insert(0, "0")
        self.ent_limit.pack(side="left", padx=5)
        
        ctk.CTkButton(self.add_frame, text="Kupon Ekle", command=self.add_coupon, fg_color="green").pack(side="left", padx=10)
        
        # List
        self.tree_frame = ctk.CTkFrame(self)
        self.tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        columns = ("code", "percent", "usage", "active")
        self.tree = ttk.Treeview(self.tree_frame, columns=columns, show="headings", height=10)
        self.tree.heading("code", text="Kod")
        self.tree.heading("percent", text="Oran (%)")
        self.tree.heading("usage", text="Kullanım / Limit")
        self.tree.heading("active", text="Durum")
        self.tree.pack(fill="both", expand=True)
        
        # Actions
        self.btn_toggle = ctk.CTkButton(self, text="Aktif/Pasif Yap", command=self.toggle_coupon, fg_color="#D35B58")
        self.btn_toggle.pack(pady=10)
        
        self.refresh_list()
        
    def add_coupon(self):
        code = self.ent_code.get().strip()
        try:
            percent = int(self.ent_percent.get())
            limit = int(self.ent_limit.get())
            if not code: return
            
            if self.db.add_coupon(code, percent, limit):
                messagebox.showinfo("Başarılı", "Kupon eklendi.")
                self.ent_code.delete(0, 'end')
                self.refresh_list()
            else:
                messagebox.showerror("Hata", "Kod zaten var.")
        except ValueError:
             messagebox.showerror("Hata", "Lütfen sayısal değer girin.")

    def refresh_list(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        for c in self.db.get_coupons():
            status = "Aktif" if c['is_active'] else "Pasif"
            usage = f"{c['used_count']} / {'∞' if c['usage_limit']==0 else c['usage_limit']}"
            self.tree.insert("", "end", values=(c['code'], c['discount_percent'], usage, status))

    def toggle_coupon(self):
        sel = self.tree.selection()
        if not sel: return
        item = self.tree.item(sel[0])
        code = item['values'][0]
        current_status = item['values'][3] == "Aktif"
        self.db.toggle_coupon(code, 0 if current_status else 1)
        self.refresh_list()

class ReportsFrame(ctk.CTkFrame):
    def __init__(self, master, db: DatabaseManager):
        super().__init__(master)
        self.db = db
        
        self.label = ctk.CTkLabel(self, text="Grafiksel Raporlar", font=("Arial", 20, "bold"))
        self.label.pack(pady=10)
        
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tabview.add("Gelir Dağılımı")
        self.tabview.add("Günlük Satış")
        
        self.btn_refresh = ctk.CTkButton(self, text="Grafikleri Yenile", command=self.draw_charts)
        self.btn_refresh.pack(pady=5)
        
        # Placeholders
        self.fig1 = None
        self.fig2 = None
        
    def draw_charts(self):
        # Clear old
        for widget in self.tabview.tab("Gelir Dağılımı").winfo_children(): widget.destroy()
        for widget in self.tabview.tab("Günlük Satış").winfo_children(): widget.destroy()
        
        # 1. Pie Chart (Coffee vs Fruit)
        coffee = self.db.get_total_income("Kahve")
        fruit = self.db.get_total_income("Kuru Meyve")
        
        if coffee + fruit > 0:
            fig1, ax1 = plt.subplots(figsize=(5, 4), dpi=100)
            ax1.pie([coffee, fruit], labels=['Kahve', 'Meyve'], autopct='%1.1f%%', colors=['#6F4E37', '#FFA500'])
            ax1.set_title("Toplam Gelir Dağılımı")
            
            canvas1 = FigureCanvasTkAgg(fig1, master=self.tabview.tab("Gelir Dağılımı"))
            canvas1.draw()
            canvas1.get_tk_widget().pack(fill="both", expand=True)
            plt.close(fig1)
        else:
            ctk.CTkLabel(self.tabview.tab("Gelir Dağılımı"), text="Henüz veri yok.").pack(pady=20)
            
        # 2. Bar Chart (Last 7 Days)
        data = self.db.get_daily_income(7) # list of (date, total)
        if data:
            dates = [d[0] for d in data]
            totals = [d[1] for d in data]
            
            fig2, ax2 = plt.subplots(figsize=(5, 4), dpi=100)
            ax2.bar(dates, totals, color='#1f538d')
            ax2.set_title("Son 7 Günlük Satış")
            plt.xticks(rotation=45)
            fig2.tight_layout()
            
            canvas2 = FigureCanvasTkAgg(fig2, master=self.tabview.tab("Günlük Satış"))
            canvas2.draw()
            canvas2.get_tk_widget().pack(fill="both", expand=True)
            plt.close(fig2)
        else:
            ctk.CTkLabel(self.tabview.tab("Günlük Satış"), text="Henüz veri yok.").pack(pady=20)

class HistoryFrame(ctk.CTkFrame):
    def __init__(self, master, db: DatabaseManager):
        super().__init__(master)
        self.db = db
        
        self.label = ctk.CTkLabel(self, text="Finansal Durum & Geçmiş", font=("Arial", 20, "bold"))
        self.label.pack(pady=10)
        
        # Summary Frame
        self.summary_frame = ctk.CTkFrame(self)
        self.summary_frame.pack(fill="x", padx=10, pady=10)
        
        self.lbl_coffee = ctk.CTkLabel(self.summary_frame, text="Kahve Geliri: 0 TL")
        self.lbl_coffee.grid(row=0, column=0, padx=20, pady=10)
        
        self.lbl_fruit = ctk.CTkLabel(self.summary_frame, text="Meyve Geliri: 0 TL")
        self.lbl_fruit.grid(row=0, column=1, padx=20, pady=10)
        
        self.lbl_expense = ctk.CTkLabel(self.summary_frame, text="Giderler: 0 TL", text_color="red")
        self.lbl_expense.grid(row=1, column=0, padx=20, pady=10)
        
        self.lbl_net = ctk.CTkLabel(self.summary_frame, text="NET KASA: 0 TL", font=("Arial", 16, "bold"), text_color="green")
        self.lbl_net.grid(row=1, column=1, padx=20, pady=10)
        
        # Actions
        self.act_frame = ctk.CTkFrame(self)
        self.act_frame.pack(fill="x", padx=10)
        self.btn_refresh = ctk.CTkButton(self.act_frame, text="Yenile", command=self.refresh_data)
        self.btn_refresh.pack(side="left", padx=10, pady=10)

        # Split Frame
        self.split_frame = ctk.CTkFrame(self)
        self.split_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Left: Kahve Tablosu
        self.left_frame = ctk.CTkFrame(self.split_frame)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=5)
        ctk.CTkLabel(self.left_frame, text="KAHVE GİDER LİSTESİ", font=("Arial", 14, "bold")).pack(pady=5)
        
        cols = ("date", "desc", "amount")
        self.tree_coffee = ttk.Treeview(self.left_frame, columns=cols, show="headings")
        self.tree_coffee.heading("date", text="Tarih")
        self.tree_coffee.heading("desc", text="Açıklama")
        self.tree_coffee.heading("amount", text="Tutar")
        self.tree_coffee.column("date", width=80)
        self.tree_coffee.column("amount", width=60)
        self.tree_coffee.pack(fill="both", expand=True)

        # Right: Meyve Tablosu
        self.right_frame = ctk.CTkFrame(self.split_frame)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=5)
        ctk.CTkLabel(self.right_frame, text="MEYVE GİDER LİSTESİ", font=("Arial", 14, "bold")).pack(pady=5)
        
        self.tree_fruit = ttk.Treeview(self.right_frame, columns=cols, show="headings")
        self.tree_fruit.heading("date", text="Tarih")
        self.tree_fruit.heading("desc", text="Açıklama")
        self.tree_fruit.heading("amount", text="Tutar")
        self.tree_fruit.column("date", width=80)
        self.tree_fruit.column("amount", width=60)
        self.tree_fruit.pack(fill="both", expand=True)
        
        # General Orders List (Delivered)
        self.orders_frame = ctk.CTkFrame(self)
        self.orders_frame.pack(fill="x", expand=False, padx=10, pady=10, side="bottom")
        
        h_frame = ctk.CTkFrame(self.orders_frame, fg_color="transparent")
        h_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(h_frame, text="SON TESLİM EDİLEN SİPARİŞLER", font=("Arial", 12, "bold")).pack(side="left", padx=10)
        ctk.CTkButton(h_frame, text="Seçili Sipariş Detayı", command=self.show_details, height=25, width=150).pack(side="right", padx=10)
        
        self.tree_orders = ttk.Treeview(self.orders_frame, columns=("id", "cust", "total", "date"), show="headings", height=5)
        self.tree_orders.heading("id", text="ID")
        self.tree_orders.heading("cust", text="Müşteri")
        self.tree_orders.heading("total", text="Tutar")
        self.tree_orders.heading("date", text="Tarih")
        self.tree_orders.pack(fill="x")
        
        self.refresh_data()
        
    def refresh_data(self):
        # Update Labels
        coffee_income = self.db.get_total_income("Kahve")
        fruit_income = self.db.get_total_income("Kuru Meyve")
        
        coffee_expenses = self.db.get_total_expenses("Kahve")
        fruit_expenses = self.db.get_total_expenses("Kuru Meyve")
        general_expenses = self.db.get_total_expenses("Genel")
        
        net_coffee = coffee_income - coffee_expenses
        net_fruit = fruit_income - fruit_expenses
        
        self.lbl_coffee.configure(text=f"Kahve (Net): {net_coffee} TL\n(Gelir: {coffee_income} - Gider: {coffee_expenses})")
        self.lbl_fruit.configure(text=f"Meyve (Net): {net_fruit} TL\n(Gelir: {fruit_income} - Gider: {fruit_expenses})")
        
        total_expenses = coffee_expenses + fruit_expenses + general_expenses
        self.lbl_expense.configure(text=f"Toplam Gider: {total_expenses} TL\n(Genel: {general_expenses})")
        
        total_net = (coffee_income + fruit_income) - total_expenses
        self.lbl_net.configure(text=f"GENEL NET: {total_net} TL")
        
        # Populate Coffee Expenses
        for item in self.tree_coffee.get_children(): self.tree_coffee.delete(item)
        for ex in self.db.get_expenses("Kahve"):
            self.tree_coffee.insert("", "end", values=(ex['created_at'], ex['description'], f"{ex['amount']} TL"))
            
        # Populate Fruit Expenses
        for item in self.tree_fruit.get_children(): self.tree_fruit.delete(item)
        for ex in self.db.get_expenses("Kuru Meyve"):
            self.tree_fruit.insert("", "end", values=(ex['created_at'], ex['description'], f"{ex['amount']} TL"))
            
        # Populate Delivered Orders
        for item in self.tree_orders.get_children(): self.tree_orders.delete(item)
        orders = self.db.get_orders("Delivered")
        for o in orders:
            self.tree_orders.insert("", "end", values=(o['id'], o['customer_name'], f"{o['total_price']} TL", o['created_at']))

    def get_selected_id(self):
        selected = self.tree_orders.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen alttaki listeden bir sipariş seçin.")
            return None
        return self.tree_orders.item(selected[0])['values'][0]

    def show_details(self):
        oid = self.get_selected_id()
        if not oid: return
        
        all_orders = self.db.get_orders("Delivered")
        order = next((o for o in all_orders if o['id'] == oid), None)
        
        if order:
            items_str = "\n".join([f"{i['quantity']}x {i['product_name']} ({i['price']} TL)" for i in order['items']])
            details = (
                f"ID: {order['id']}\n"
                f"Müşteri: {order['customer_name']}\n\n"
                f"--- Ürünler ---\n{items_str}\n\n"
                f"Toplam: {order['total_price']} TL"
            )
            if order.get('coupon_code'):
                details += f"\n🎟️ Kupon: {order['coupon_code']} (-{order['discount_amount']} TL)"
            messagebox.showinfo("Geçmiş Sipariş Detayı", details)

    def open_expense_popup(self):
        top = ctk.CTkToplevel(self)
        top.title("Gider Ekle")
        top.geometry("300x350")
        
        ctk.CTkLabel(top, text="Kategori:").pack(pady=5)
        cat_var = ctk.StringVar(value="Genel")
        ctk.CTkOptionMenu(top, variable=cat_var, values=["Kahve", "Kuru Meyve", "Genel"]).pack(pady=5)
        
        ctk.CTkLabel(top, text="Açıklama:").pack(pady=5)
        ent_desc = ctk.CTkEntry(top)
        ent_desc.pack(pady=5)
        
        ctk.CTkLabel(top, text="Tutar:").pack(pady=5)
        ent_amount = ctk.CTkEntry(top)
        ent_amount.pack(pady=5)
        
        def add():
            try:
                desc = ent_desc.get()
                amt = float(ent_amount.get())
                cat = cat_var.get()
                if not desc:
                    messagebox.showerror("Hata", "Açıklama giriniz.")
                    return
                self.db.add_expense(cat, desc, amt)
                messagebox.showinfo("Başarılı", "Gider eklendi.")
                self.refresh_data()
                top.destroy()
            except ValueError:
                messagebox.showerror("Hata", "Geçersiz tutar.")
                
        ctk.CTkButton(top, text="Kaydet", command=add, fg_color="#D35B58").pack(pady=20)

class SettingsFrame(ctk.CTkFrame):
    def __init__(self, master, db: DatabaseManager):
        super().__init__(master)
        self.db = db
        
        self.label = ctk.CTkLabel(self, text="Ayarlar", font=("Arial", 20, "bold"))
        self.label.pack(pady=10)
        
        ctk.CTkLabel(self, text="IBAN Mesajı (Markdown destekli):").pack(anchor="w", padx=20)
        self.txt_iban = ctk.CTkTextbox(self, height=150)
        self.txt_iban.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(self, text="Karşılama Mesajı:").pack(anchor="w", padx=20, pady=(20, 0))
        self.txt_welcome = ctk.CTkTextbox(self, height=100)
        self.txt_welcome.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(self, text="Admin ID:").pack(anchor="w", padx=20, pady=(20, 0))
        self.ent_admin = ctk.CTkEntry(self)
        self.ent_admin.pack(fill="x", padx=20, pady=5)
        
        self.btn_save = ctk.CTkButton(self, text="Ayarları Kaydet", command=self.save_settings)
        self.btn_save.pack(pady=20)
        
        self.load_settings()
        
    def load_settings(self):
        self.txt_iban.insert("1.0", self.db.get_setting("iban_message"))
        self.txt_welcome.insert("1.0", self.db.get_setting("welcome_message"))
        self.ent_admin.insert(0, self.db.get_setting("admin_id"))
        
    def save_settings(self):
        iban = self.txt_iban.get("1.0", "end-1c")
        welcome = self.txt_welcome.get("1.0", "end-1c")
        admin = self.ent_admin.get()
        
        self.db.set_setting("iban_message", iban)
        self.db.set_setting("welcome_message", welcome)
        self.db.set_setting("admin_id", admin)
        messagebox.showinfo("Başarılı", "Ayarlar kaydedildi.")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sipariş Yönetim Paneli")
        self.geometry("1100x700")
        
        self.db = DatabaseManager()
        
        # Layout: Grid 1x2 (Sidebar, Main)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="Filtresso\nAdmin", font=("Arial", 20, "bold"))
        self.logo_label.pack(pady=30)
        
        self.btn_orders = ctk.CTkButton(self.sidebar, text="Siparişler", command=lambda: self.show_frame("orders"))
        self.btn_orders.pack(pady=10, padx=20)
        
        self.btn_products = ctk.CTkButton(self.sidebar, text="Ürünler", command=lambda: self.show_frame("products"))
        self.btn_products.pack(pady=10, padx=20)
        
        self.btn_history = ctk.CTkButton(self.sidebar, text="Geçmiş / Kasa", command=lambda: self.show_frame("history"))
        self.btn_history.pack(pady=10, padx=20)

        self.btn_coupons = ctk.CTkButton(self.sidebar, text="Kuponlar", command=lambda: self.show_frame("coupons"))
        self.btn_coupons.pack(pady=10, padx=20)
        
        self.btn_reports = ctk.CTkButton(self.sidebar, text="Raporlar", command=lambda: self.show_frame("reports"))
        self.btn_reports.pack(pady=10, padx=20)
        
        self.btn_settings = ctk.CTkButton(self.sidebar, text="Ayarlar", command=lambda: self.show_frame("settings"))
        self.btn_settings.pack(pady=10, padx=20)
        
        # Main Area
        self.frames = {}
        self.frames["orders"] = OrdersFrame(self, self.db)
        self.frames["products"] = ProductsFrame(self, self.db)
        self.frames["history"] = HistoryFrame(self, self.db)
        self.frames["coupons"] = CouponsFrame(self, self.db)
        self.frames["reports"] = ReportsFrame(self, self.db)
        self.frames["settings"] = SettingsFrame(self, self.db)
        
        self.show_frame("orders")
        
    def show_frame(self, name):
        # Hide all
        for frame in self.frames.values():
            frame.grid_forget()
        
        # Show selected
        self.frames[name].grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        # Optional: trigger render for reports
        if name == "reports":
            self.frames["reports"].draw_charts()

if __name__ == "__main__":
    app = App()
    app.mainloop()
