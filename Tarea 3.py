import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta


BG_LIGHT = "#f6f7fb"
CARD = "#ffffff"
PRIMARY = "#111111"
ACCENT = "#4f46e5"
TEXT_GRAY = "#666666"

BG_DARK = "#18181b"
CARD_DARK = "#27272a"


class AppTareas:

    def __init__(self, root):
        self.root = root
        self.root.title("ORGANIZADOR UI")
        self.root.geometry("560x650")
        self.root.resizable(False, False)

        self.dark = False
        self.tareas = []

        self.root.configure(bg=BG_LIGHT)

        header = tk.Frame(root, bg=PRIMARY, height=90)
        header.pack(fill="x")

        tk.Label(header,
                 text="organizador",
                 fg="white",
                 bg=PRIMARY,
                 font=("Segoe UI",20,"bold")).pack(pady=(18,0))

        tk.Label(header,
                 text="Organiza tu día como una app moderna",
                 fg="#cccccc",
                 bg=PRIMARY,
                 font=("Segoe UI",10)).pack()

    
        self.card = tk.Frame(root, bg=CARD)
        self.card.place(x=30, y=110, width=500, height=500)

   
        self.entry = tk.Entry(self.card, font=("Segoe UI",12), bd=0,
                              highlightthickness=1, highlightbackground="#ddd")
        self.entry.place(x=20,y=20,width=200,height=32)

        self.fecha = tk.Entry(self.card, font=("Segoe UI",11), bd=0,
                              highlightthickness=1, highlightbackground="#ddd")
        self.fecha.insert(0,"AAAA-MM-DD")
        self.fecha.place(x=230,y=20,width=110,height=32)

        self.categoria = ttk.Combobox(self.card,
                                      values=["Trabajo","Personal","Escuela"],
                                      width=12)
        self.categoria.place(x=350,y=20,height=32)
        self.categoria.set("Personal")


        self.btn_add = tk.Button(self.card,text="Agregar",
                                 bg=ACCENT,fg="white",
                                 font=("Segoe UI",10,"bold"),
                                 bd=0,command=self.agregar)
        self.btn_add.place(x=20,y=60,width=120,height=32)

        tk.Button(self.card,text="Editar",
                  bg="#e5e7eb",bd=0,
                  command=self.editar).place(x=150,y=60,width=90,height=32)

        tk.Button(self.card,text="Eliminar",
                  bg="#ef4444",fg="white",bd=0,
                  command=self.eliminar_animado).place(x=250,y=60,width=90,height=32)

        tk.Button(self.card,text="🌙",
                  bg="#e5e7eb",bd=0,
                  command=self.toggle_dark).place(x=350,y=60,width=50,height=32)

        self.lista = tk.Listbox(self.card,
                                font=("Segoe UI",11),
                                bd=0,
                                highlightthickness=0)
        self.lista.place(x=20,y=110,width=460,height=320)

        self.info = tk.Label(self.card,text="",bg=CARD,fg=TEXT_GRAY,font=("Segoe UI",10))
        self.info.place(x=20,y=440)


    def agregar(self):
        texto = self.entry.get()
        fecha = self.fecha.get()
        cat = self.categoria.get()

        if texto == "":
            return

        self.tareas.append((texto,fecha,cat))
        self.actualizar()

        self.entry.delete(0,tk.END)

    def actualizar(self):
        self.lista.delete(0,tk.END)
        hoy = datetime.now()

        for t in self.tareas:
            texto,fecha,cat = t
            linea = f"{texto}  •  {cat}  •  {fecha}"

            try:
                fecha_dt = datetime.strptime(fecha,"%Y-%m-%d")
                if fecha_dt - hoy <= timedelta(days=2):
                    linea += "  ⚠️"
            except:
                pass

            self.lista.insert(tk.END,linea)

    def editar(self):
        if not self.lista.curselection():
            return
        i = self.lista.curselection()[0]
        texto,fecha,cat = self.tareas[i]

        self.entry.delete(0,tk.END)
        self.entry.insert(0,texto)
        self.fecha.delete(0,tk.END)
        self.fecha.insert(0,fecha)
        self.categoria.set(cat)

        del self.tareas[i]
        self.actualizar()

 
    def eliminar_animado(self):
        if not self.lista.curselection():
            return
        self.info.config(text="Eliminando...")
        self.root.after(400,self.eliminar)

    def eliminar(self):
        if not self.lista.curselection():
            return
        i = self.lista.curselection()[0]
        del self.tareas[i]
        self.info.config(text="")
        self.actualizar()

    def toggle_dark(self):
        self.dark = not self.dark

        if self.dark:
            self.root.configure(bg=BG_DARK)
            self.card.configure(bg=CARD_DARK)
            self.info.configure(bg=CARD_DARK,fg="white")
            self.lista.configure(bg=CARD_DARK,fg="white")
        else:
            self.root.configure(bg=BG_LIGHT)
            self.card.configure(bg=CARD)
            self.info.configure(bg=CARD,fg=TEXT_GRAY)
            self.lista.configure(bg=CARD,fg="black")

root = tk.Tk()
app = AppTareas(root)
root.mainloop()
