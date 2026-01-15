import sys
import os
import tkinter as tk
from tkinter import ttk
from tkinterdnd2 import TkinterDnD, DND_FILES
import threading
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
        
        # Unify size option
        self.unify_var = tk.BooleanVar(value=False)
        self.unify_check = tk.Checkbutton(
            options_frame, 
            text="Unify to smallest size", 
            variable=self.unify_var,
            fg="#fff", bg="#2b2b2b", selectcolor="#3c3c3c",
            activebackground="#2b2b2b", activeforeground="#fff"
        )
        self.unify_check.grid(row=1, column=0, columnspan=2, sticky="w", pady=(5, 0))
        
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
        
        thread = threading.Thread(target=self.process_files, args=(png_files, min_size, unify))
        thread.start()

    def update_progress(self, current, total, message):
        """Callback for progress updates from split_images."""
        percent = (current / total) * 100 if total > 0 else 0
        self.after(0, lambda: self.progress.configure(value=percent))
        self.after(0, lambda: self.status_label.configure(text=message))

    def process_files(self, files, min_size, unify):
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
