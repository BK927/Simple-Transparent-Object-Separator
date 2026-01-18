import sys
import os
import tkinter as tk
from tkinter import ttk
from tkinterdnd2 import TkinterDnD, DND_FILES
import threading
from PIL import Image
import split_images

class App(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simple Transparent Object Separator")
        self.geometry("400x350")
        self.configure(bg="#2b2b2b")
        
        # Options frame
        options_frame = tk.Frame(self, bg="#2b2b2b")
        options_frame.pack(fill="x", padx=20, pady=(15, 5))
        
        # Min size option
        tk.Label(options_frame, text="Min Size (px):", fg="#fff", bg="#2b2b2b").grid(row=0, column=0, sticky="w")
        self.min_size_var = tk.StringVar(value="128")
        self.min_size_entry = tk.Entry(options_frame, textvariable=self.min_size_var, width=8)
        self.min_size_entry.grid(row=0, column=1, padx=5)
        
        # Unification Group
        self.unify_frame = tk.LabelFrame(options_frame, text="Unification Settings", fg="#fff", bg="#2b2b2b", padx=10, pady=10)
        self.unify_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
        # Unify size option (Master Toggle)
        self.unify_var = tk.BooleanVar(value=False)
        self.unify_check = tk.Checkbutton(
            self.unify_frame, 
            text="Enable Unification", 
            variable=self.unify_var,
            command=self.toggle_unify_options, # Add toggle command
            fg="#fff", bg="#2b2b2b", selectcolor="#3c3c3c",
            activebackground="#2b2b2b", activeforeground="#fff"
        )
        self.unify_check.grid(row=0, column=0, columnspan=2, sticky="w")
        
        # Resize Algorithm option
        self.algo_label = tk.Label(self.unify_frame, text="Resize Algo:", fg="#fff", bg="#2b2b2b")
        self.algo_label.grid(row=1, column=0, sticky="w", pady=(5, 0))
        
        self.algo_var = tk.StringVar(value="LANCZOS")
        self.algo_combo = ttk.Combobox(
            self.unify_frame, 
            textvariable=self.algo_var,
            values=[
                "LANCZOS", "BICUBIC", "BILINEAR", "BOX", "NEAREST", "HAMMING",
                "Nearest Neighbor", "Sharp Bilinear", "Area Sampling"
            ],
            state="readonly",
            width=15
        )
        self.algo_combo.grid(row=1, column=1, padx=5, pady=(5, 0), sticky="w")
        
        # Unify Criteria option
        self.criteria_label = tk.Label(self.unify_frame, text="Criteria:", fg="#fff", bg="#2b2b2b")
        self.criteria_label.grid(row=2, column=0, sticky="w", pady=(5, 0))
        
        self.criteria_var = tk.StringVar(value="smaller")
        
        self.criteria_frame = tk.Frame(self.unify_frame, bg="#2b2b2b")
        self.criteria_frame.grid(row=2, column=1, padx=5, pady=(5, 0), sticky="w")
        
        self.criteria_radios = []
        r1 = tk.Radiobutton(self.criteria_frame, text="Box", variable=self.criteria_var, value="smaller",
                      fg="#fff", bg="#2b2b2b", selectcolor="#3c3c3c", activebackground="#2b2b2b", activeforeground="#fff")
        r1.pack(side="left")
        self.criteria_radios.append(r1)
        
        r2 = tk.Radiobutton(self.criteria_frame, text="Width", variable=self.criteria_var, value="width",
                      fg="#fff", bg="#2b2b2b", selectcolor="#3c3c3c", activebackground="#2b2b2b", activeforeground="#fff")
        r2.pack(side="left")
        self.criteria_radios.append(r2)
        
        r3 = tk.Radiobutton(self.criteria_frame, text="Height", variable=self.criteria_var, value="height",
                      fg="#fff", bg="#2b2b2b", selectcolor="#3c3c3c", activebackground="#2b2b2b", activeforeground="#fff")
        r3.pack(side="left")
        self.criteria_radios.append(r3)
        
        # Initialize state
        self.toggle_unify_options()
        
        # Drop area
        self.label = tk.Label(
            self,
            text="Drag & Drop\nPNG files here",
            font=("Segoe UI", 16),
            fg="#ffffff",
            bg="#3c3c3c",
            relief="groove",
            bd=2
        )
        self.label.pack(fill="both", expand=True, padx=20, pady=15)
        
        self.label.drop_target_register(DND_FILES)
        self.label.dnd_bind('<<Drop>>', self.on_drop)
        
        # Progress bar
        self.progress = ttk.Progressbar(self, mode='determinate', length=360)
        self.progress.pack(padx=20, pady=(0, 15))
        
        # Status label
        self.status_label = tk.Label(self, text="", fg="#aaa", bg="#2b2b2b", font=("Segoe UI", 9))
        self.status_label.pack(pady=(0, 10))

    def toggle_unify_options(self):
        """Enables or disables unification options based on the checkbox."""
        state = "normal" if self.unify_var.get() else "disabled"
        gray_state = "readonly" if self.unify_var.get() else "disabled"
        
        self.algo_combo.config(state=gray_state)
        for rb in self.criteria_radios:
            rb.config(state=state)
            
        # Optional: Dim labels (change color) if desired, but state is usually enough.
        # color = "#fff" if self.unify_var.get() else "#777"
        # self.algo_label.config(fg=color)
        # self.criteria_label.config(fg=color)

    def on_drop(self, event):
        files = self.tk.splitlist(event.data)
        png_files = [f for f in files if f.lower().endswith('.png')]
        
        if not png_files:
            self.label.config(text="No PNG files dropped.")
            return
        
        self.label.config(text=f"Processing...")
        self.progress['value'] = 0
        
        try:
            min_size = int(self.min_size_var.get())
        except ValueError:
            min_size = 128
        
        unify = self.unify_var.get()
        
        algo_name = self.algo_var.get()
        algo_map = {
            "LANCZOS": Image.Resampling.LANCZOS,
            "BICUBIC": Image.Resampling.BICUBIC,
            "BILINEAR": Image.Resampling.BILINEAR,
            "BOX": Image.Resampling.BOX,
            "NEAREST": Image.Resampling.NEAREST,
            "HAMMING": Image.Resampling.HAMMING,
            "Nearest Neighbor": Image.Resampling.NEAREST,
            "Sharp Bilinear": Image.Resampling.HAMMING,
            "Area Sampling": Image.Resampling.BOX,
        }
        resample_filter = algo_map.get(algo_name, Image.Resampling.LANCZOS)
        
        unify_mode = self.criteria_var.get()

        thread = threading.Thread(target=self.process_files, args=(png_files, min_size, unify, resample_filter, unify_mode))
        thread.start()

    def update_progress(self, current, total, message):
        """Callback for progress updates from split_images."""
        percent = (current / total) * 100 if total > 0 else 0
        self.after(0, lambda: self.progress.configure(value=percent))
        self.after(0, lambda: self.status_label.configure(text=message))

    def process_files(self, files, min_size, unify, resample_filter, unify_mode):
        try:
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.getcwd()
            output_dir = os.path.join(base_dir, "output")
            
            split_images.split_images(
                files, 
                output_dir=output_dir, 
                min_size=min_size, 
                unify=unify,
                resample_filter=resample_filter,
                unify_mode=unify_mode,
                progress_callback=self.update_progress
            )
            self.after(0, lambda: self.label.config(text="Done!"))
            self.after(0, lambda: self.progress.configure(value=100))
            self.after(0, lambda: self.status_label.configure(text=""))
        except Exception as e:
            self.after(0, lambda: self.label.config(text=f"Error: {str(e)}"))

if __name__ == "__main__":
    app = App()
    app.mainloop()
