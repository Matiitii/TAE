import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox, simpledialog, filedialog
import json
import os
from datetime import datetime, timedelta




from PIL import Image, ImageDraw, ImageFont

# Ruta a la fuente .otf que subiste
font_path = "/mnt/data/Coolvetica Rg.otf"

# Crear una imagen en blanco
image = Image.new("RGB", (800, 200), color=(255, 255, 255))

# Cargar la fuente
font = ImageFont.truetype(font_path, size=60)

# Dibujar el texto
draw = ImageDraw.Draw(image)
draw.text((50, 70), "Texto con Coolvetica!", font=font, fill=(0, 0, 0))

# Guardar la imagen
image.save("/mnt/data/texto_con_coolvetica.png")


# Paleta moderna con modo claro/oscuro
MODE = 'light'
COLORS = {
    'light': {
        'BG_PRIMARY': "#F4F6F7",
        'BG_ACCENT': "#D0D3D4",
        'CARD_COLOR': "#FFFFFF",
        'FG_TEXT': "#2C3E50",
        'BTN_COLOR': "#A9CCE3",
        'BTN_ACTIVE': "#5499C7"
    },
    'dark': {
        'BG_PRIMARY': "#2C3E50",
        'BG_ACCENT': "#2C3E50",
        'CARD_COLOR': "#3B4B5A",
        'FG_TEXT': "#ECF0F1",
        'BTN_COLOR': "#5DADE2",
        'BTN_ACTIVE': "#2980B9"
    }
}

def get_color(name):
    return COLORS[MODE][name]

DATA_FILE = 'products.json'
SALES_FILE = 'sales.json'
SETTINGS_FILE = 'settings.json'
CONFIG_FILE = 'config.json'

class Product:
    def __init__(self, name, price, stock, margin_pct):
        self.name = name
        self.price = int(price)
        self.stock = int(stock)
        self.margin_pct = float(margin_pct)

    def to_dict(self):
        return vars(self)

    @classmethod
    def from_dict(cls, d):
        return cls(d['name'], d['price'], d['stock'], d.get('margin_pct', 0))

class ShopApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.settings = self.load_settings()
        self.config = self.load_config()
        self.sales = []
        self.products = []
        self.selected = {}

        self.title("Tienda / Digital Drive")
        self.geometry("900x700")
        self.configure(bg=get_color('BG_PRIMARY'))
        self._create_styles()
        self._build_ui()

        self.load_sales()
        self.load_products()
        self.update_clock()

    def _create_styles(self):
        style = ttk.Style(self)
        style.theme_use('default')
        style.configure("TFrame", background=get_color('BG_PRIMARY'))
        style.configure("Accent.TFrame", background=get_color('BG_ACCENT'))
        style.configure("Card.TFrame", background=get_color('CARD_COLOR'))
        style.configure("TLabel", background=get_color('BG_PRIMARY'), foreground=get_color('FG_TEXT'), font=("Helvetica", 16))
        style.configure("Header.TLabel", background=get_color('BG_ACCENT'), foreground=get_color('FG_TEXT'), font=("Helvetica", 32, "bold"))
        style.configure("Accent.TLabel", background=get_color('BG_ACCENT'), foreground=get_color('FG_TEXT'), font=("Helvetica", 20, "bold"))
        style.configure("TButton", font=("Helvetica", 16), padding=10, background=get_color('BTN_COLOR'))
        style.map("TButton",
                  background=[("active", get_color('BTN_ACTIVE'))],
                  foreground=[("active", get_color('FG_TEXT'))])
        default = tkfont.nametofont("TkDefaultFont"); default.configure(size=16)

    def _build_ui(self):
        self.header = ttk.Frame(self, style="Accent.TFrame", height=80)
        self.header.pack(side="top", fill="x")
        ttk.Label(self.header, text="Tienda", style="Header.TLabel").pack(side="left", padx=30)
        self.clock_lbl = ttk.Label(self.header, style="Header.TLabel")
        self.clock_lbl.pack(side="right", padx=30)

        sidebar = ttk.Frame(self, width=120, style="Accent.TFrame")
        sidebar.pack(side="left", fill="y")
        icons = [
            ("$", self.show_earnings),
            ("+", self.on_add),
            ("🔍", self.on_search),
            ("⚙", self.on_configure)
        ]
        for ico, cmd in icons:
            ttk.Button(sidebar, text=ico, style="TButton", command=cmd).pack(pady=20, padx=10)

        self.main = ttk.Frame(self, style="TFrame")
        self.main.pack(side="left", fill="both", expand=True, padx=20, pady=20)

        metrics = ttk.Frame(self.main, style="Accent.TFrame", padding=15)
        metrics.pack(fill="x", pady=(0,15))
        self.lbl_sales = ttk.Label(metrics, text="Ganancias: $0", style="Accent.TLabel")
        self.lbl_stock = ttk.Label(metrics, text="Stock total: 0", style="Accent.TLabel")
        self.lbl_sales.grid(row=0, column=0, padx=20)
        self.lbl_stock.grid(row=0, column=1, padx=20)

        actions = ttk.Frame(self.main, padding=10)
        actions.pack(fill="x", pady=(0,15))
        for text, cmd in [
            ("Registrar venta", self.mark_sales),
            ("Reponer stock", self.replenish_stock),
            ("Refrescar", self.on_refresh),
            ("Agregar producto", self.on_add),
            ("Eliminar seleccionados", self.on_delete),
        ]:
            ttk.Button(actions, text=text, command=cmd).pack(side="left", padx=10)

        self.canvas = tk.Canvas(self.main, bg=get_color('BG_PRIMARY'), highlightthickness=0)
        vsb = ttk.Scrollbar(self.main, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y", padx=(0,10))
        self.canvas.pack(side="left", fill="both", expand=True)
        self.list_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0,0), window=self.list_frame, anchor="nw")
        self.list_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

    def update_clock(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.clock_lbl.config(text=now)
        self.after(1000, self.update_clock)

    def on_search(self):
        term = simpledialog.askstring("Buscar", "Ingrese nombre o parte del producto:", parent=self)
        if not term:
            return
        term = term.lower()
        for idx, p in enumerate(self.products):
            if term in p.name.lower():
                # desplazar
                widget = self.list_frame.grid_slaves(row=idx, column=0)[0]
                self.canvas.yview_moveto(widget.winfo_y()/self.list_frame.winfo_height())
                return
        messagebox.showinfo("Buscar", "Producto no encontrado.", parent=self)

    def load_settings(self):
        if os.path.isfile(SETTINGS_FILE):
            return json.load(open(SETTINGS_FILE))
        return {'fixed_margin_pct': None}

    def save_settings(self):
        json.dump(self.settings, open(SETTINGS_FILE,'w'), indent=2)

    def load_config(self):
        if os.path.isfile(CONFIG_FILE):
            return json.load(open(CONFIG_FILE))
        return {'dollar_value':1000, 'expenses':{}}

    def save_config(self):
        json.dump(self.config, open(CONFIG_FILE,'w'), indent=2)

    def load_products(self):
        if os.path.isfile(DATA_FILE):
            self.products = [Product.from_dict(d) for d in json.load(open(DATA_FILE))]
        self.refresh_ui()

    def save_products(self):
        json.dump([p.to_dict() for p in self.products], open(DATA_FILE,'w'), indent=2)

    def load_sales(self):
        try:
            content = open(SALES_FILE).read().strip() if os.path.isfile(SALES_FILE) else ''
            self.sales = json.loads(content) if content else []
        except:
            self.sales = []
        self.update_metrics()

    def save_sales(self):
        json.dump(self.sales, open(SALES_FILE,'w'), indent=2)

    def refresh_ui(self):
        self.selected.clear()
        self.lbl_stock.config(text=f"Stock total: {sum(p.stock for p in self.products)}")
        self.update_metrics()
        for w in self.list_frame.winfo_children(): w.destroy()
        for idx,p in enumerate(self.products):
            var=tk.IntVar(); self.selected[idx]=var
            frame=ttk.Frame(self.list_frame,style="Card.TFrame",padding=15)
            frame.grid(row=idx,column=0,pady=10,sticky="ew")
            ttk.Label(frame,text=f"{p.name} | ${p.price} | Stock: {p.stock} | Margen de ganancia: {p.margin_pct}%").pack(anchor="w")
            tk.Checkbutton(frame, variable=var).pack(anchor="e")
        self.canvas.yview_moveto(0)

    def update_metrics(self):
        now=datetime.now();earn=0
        for s in self.sales:
            try:
                t=datetime.fromisoformat(s['timestamp'])
                if now-t<=timedelta(days=1): earn+=s['qty']*s['price']*(s['margin_pct']/100)
            except: pass
        self.lbl_sales.config(text=f"Ganancias: ${int(earn)}")

    def on_refresh(self):
        self.load_sales(); self.load_products()

    def on_add(self):
        name=simpledialog.askstring("Nombre","Nombre del producto:",parent=self)
        if not name: return
        price=simpledialog.askinteger("Precio","Precio en ARS:",parent=self)
        if price is None: return
        stock=simpledialog.askinteger("Stock","Cantidad en inventario:",parent=self)
        if stock is None: return
        if self.settings.get('fixed_margin_pct') is None:
            margin=simpledialog.askfloat("Margen de ganancia (%)","Margen de ganancia (%):",parent=self)
            if margin is None: return
        else:
            margin=self.settings['fixed_margin_pct']
        self.products.append(Product(name,price,stock,margin))
        self.save_products(); self.refresh_ui()

    def replenish_stock(self):
        idxs=[i for i,v in self.selected.items() if v.get()]
        if not idxs: messagebox.showwarning("Reponer","Selecciona producto(s)",parent=self);return
        for i in idxs:
            amt=simpledialog.askinteger("Reponer","Cantidad a sumar:",parent=self)
            if amt and amt>0: self.products[i].stock+=amt
        self.save_products(); self.refresh_ui()

    def on_delete(self):
        idxs=[i for i,v in self.selected.items() if v.get()]
        if not idxs: messagebox.showwarning("Eliminar","Selecciona producto(s)",parent=self);return
        for i in sorted(idxs,reverse=True): del self.products[i]
        self.save_products(); self.refresh_ui()

    def on_configure(self):
        win = tk.Toplevel(self)
        win.title("Configuración")
        win.geometry("400x550")
        win.configure(bg=get_color('BG_PRIMARY'))
        win.grab_set()

        # Valor del dólar
        ttk.Label(win, text="Valor del dólar actual:", font=("Segoe UI", 12)).pack(pady=5)
        dolar_var = tk.IntVar(value=self.config.get('dollar_value', 1000))
        ttk.Entry(win, textvariable=dolar_var).pack(fill='x', padx=20)

        # Gastos mensuales
        ttk.Label(win, text="Gasto mensual (YYYY-MM):", font=("Segoe UI", 12)).pack(pady=(20,5))
        now_month = datetime.now().strftime("%Y-%m")
        gasto_var = tk.IntVar(value=self.config['expenses'].get(now_month, 0))
        ttk.Entry(win, textvariable=gasto_var).pack(fill='x', padx=20)

        # Modo oscuro
        ttk.Label(win, text="Modo oscuro:", font=("Segoe UI", 12)).pack(pady=(20,5))
        dark_var = tk.BooleanVar(value=(MODE == 'dark'))
        ttk.Checkbutton(win, text="Activar", variable=dark_var).pack()

        # Margen de ganancia
        ttk.Label(win, text="Margen de ganancia:", font=("Segoe UI", 12)).pack(pady=(20,5))
        mode_var = tk.StringVar(value='fixed' if self.settings.get('fixed_margin_pct') is not None else 'custom')
        ttk.Radiobutton(win, text="Fijo", variable=mode_var, value='fixed').pack(anchor='w', padx=20)
        ttk.Radiobutton(win, text="Personalizado por producto", variable=mode_var, value='custom').pack(anchor='w', padx=20)
        margin_var = tk.DoubleVar(value=self.settings.get('fixed_margin_pct') or 0)
        ttk.Entry(win, textvariable=margin_var).pack(fill='x', padx=20, pady=(5,20))

        def save():
            global MODE
            # Config generales
            self.config['dollar_value'] = dolar_var.get()
            self.config['expenses'][now_month] = gasto_var.get()
            MODE = 'dark' if dark_var.get() else 'light'
            self.save_config()
            # Margen settings
            if mode_var.get() == 'fixed':
                self.settings['fixed_margin_pct'] = float(margin_var.get())
                # aplicar a todos los productos
                for p in self.products:
                    p.margin_pct = self.settings['fixed_margin_pct']
                self.save_products()
            else:
                self.settings['fixed_margin_pct'] = None
            self.save_settings()
            win.destroy()
            self.configure(bg=get_color('BG_PRIMARY'))
            self._create_styles()
            self.refresh_ui()

        ttk.Button(win, text="Guardar", command=save).pack(pady=10)

    def show_earnings(self):
        now=datetime.now();d24=w=m=0
        for s in self.sales:
            try:
                t=datetime.fromisoformat(s['timestamp']);amt=s['qty']*s['price']*(s['margin_pct']/100)
                if now-t<=timedelta(days=1): d24+=amt
                if now-t<=timedelta(days=7): w+=amt
                if now-t<=timedelta(days=30): m+=amt
            except: pass
        msg=f"Ganancias:\n24h:${int(d24)}\nSemana:${int(w)}\nMes:${int(m)}"
        messagebox.showinfo("Ganancias",msg,parent=self)

    def mark_sales(self):
        idxs=[i for i,v in self.selected.items() if v.get()]
        if not idxs: messagebox.showwarning("Venta","Selecciona producto(s)",parent=self);return
        for i in idxs:
            p=self.products[i]
            qty=simpledialog.askinteger("Venta",f"Unidades vendidas de '{p.name}' (stock:{p.stock}):",parent=self,minvalue=1,maxvalue=p.stock)
            if qty:
                p.stock-=qty
                self.sales.append({'name':p.name,'qty':qty,'price':p.price,'margin_pct':p.margin_pct,'timestamp':datetime.now().isoformat()})
        self.save_products(); self.save_sales(); self.refresh_ui()

if __name__=='__main__':
    ShopApp().mainloop()
