import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from tkinter import ttk
import yt_dlp as youtube_dl
import threading
import os
import queue
import sys
from PIL import Image, ImageTk
import re
import random

class YouTubeDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TubeMaster Pro")
        self.root.config(bg="#e0e0e0")
        # Cargar el icono
        icon = ImageTk.PhotoImage(file='assets/logo.ico')

        # Establecer el icono de la ventana
        self.root.iconphoto(True, icon)

        self.queue = queue.Queue()
        self.downloads = {}  # Inicializar downloads aquí
        self.downloaded_files = {}
        self.create_widgets()
        self.update_queue()
        self.increment_progress()

        # Definir la ubicación de ffmpeg en la misma carpeta que el script en ejecución
        self.ffmpeg_location = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ffmpeg.exe')

        if not os.path.isfile(self.ffmpeg_location):
            print(f"WARNING: ffmpeg-location {self.ffmpeg_location} does not exist! Continuing without ffmpeg")
        else:
            print(f"ffmpeg found at {self.ffmpeg_location}")

    def create_widgets(self):
        # Cargar las imágenes
        add_image = ImageTk.PhotoImage(Image.open("assets/add_button.png").resize((50, 50), Image.LANCZOS))
        clear_image = ImageTk.PhotoImage(Image.open("assets/clear_button.png").resize((50, 50), Image.LANCZOS))
        download_image = ImageTk.PhotoImage(Image.open("assets/download_button.png").resize((50, 50), Image.LANCZOS))
        clean_completed_image = ImageTk.PhotoImage(Image.open("assets/clean_completed_button.png").resize((50, 50), Image.LANCZOS))
        logo_image = ImageTk.PhotoImage(Image.open("assets/logo.png").resize((210, 80), Image.LANCZOS))  # Añadido para el logo

        # Crear frame para el logo
        logo_frame = tk.Frame(self.root, bg="#e0e0e0")
        logo_frame.grid(row=0, column=0, pady=5)
        logo_label = tk.Label(logo_frame, image=logo_image, bg="#e0e0e0")
        logo_label.image = logo_image  # Guardar referencia para evitar garbage collection
        logo_label.pack()

        # Crear botones con imágenes y descripciones
        button_frame = tk.Frame(self.root, bg="#e0e0e0")
        button_frame.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky="e")

        # Agregar URL
        add_button_frame = tk.Frame(button_frame, bg="#e0e0e0")
        add_button_frame.pack(side=tk.LEFT, padx=10)
        self.add_button = tk.Button(add_button_frame, image=add_image, command=self.add_url, bg="#e0e0e0", borderwidth=0)
        self.add_button.image = add_image  # Guardar referencia para evitar garbage collection
        self.add_button.pack(side=tk.TOP, pady=(0, 5))
        tk.Label(add_button_frame, text="Agregar URL", bg="#e0e0e0", fg="black").pack(side=tk.TOP)

        # Limpiar URLs
        clean_button_frame = tk.Frame(button_frame, bg="#e0e0e0")
        clean_button_frame.pack(side=tk.LEFT, padx=10)
        self.clean_button = tk.Button(clean_button_frame, image=clear_image, command=self.clean_urls, bg="#e0e0e0", borderwidth=0)
        self.clean_button.image = clear_image
        self.clean_button.pack(side=tk.TOP, pady=(0, 5))
        tk.Label(clean_button_frame, text="Limpiar URLs", bg="#e0e0e0", fg="black").pack(side=tk.TOP)

        # Opciones de Descarga
        download_button_frame = tk.Frame(button_frame, bg="#e0e0e0")
        download_button_frame.pack(side=tk.LEFT, padx=10)
        self.download_button = tk.Button(download_button_frame, image=download_image, command=self.open_download_options, bg="#e0e0e0", borderwidth=0)
        self.download_button.image = download_image
        self.download_button.pack(side=tk.TOP, pady=(0, 5))
        tk.Label(download_button_frame, text="Descargar", bg="#e0e0e0", fg="black").pack(side=tk.TOP)

        # Limpiar Descargas Completadas
        clean_completed_button_frame = tk.Frame(button_frame, bg="#e0e0e0")
        clean_completed_button_frame.pack(side=tk.LEFT, padx=10)
        self.clean_completed_button = tk.Button(clean_completed_button_frame, image=clean_completed_image, command=self.clean_completed_downloads, bg="#e0e0e0", borderwidth=0)
        self.clean_completed_button.image = clean_completed_image
        self.clean_completed_button.pack(side=tk.TOP, pady=(0, 5))
        tk.Label(clean_completed_button_frame, text="Limpiar Completadas", bg="#e0e0e0", fg="black").pack(side=tk.TOP)

        self.url_listbox = tk.Listbox(self.root, selectmode=tk.MULTIPLE, width=80, bg="#FFFFFF", fg="black")
        self.url_listbox.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

        self.active_downloads_label = tk.Label(self.root, text="Descargas activas:", bg="#e0e0e0", fg="black", font="Helvica 13")
        self.active_downloads_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")

        self.active_downloads_frame = tk.Frame(self.root, bg="#e0e0e0")
        self.active_downloads_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")



    def starts_with_http(self, url):
        return url.startswith("http://") or url.startswith("https://")

    def add_url(self):
        url = self.root.clipboard_get()  # Obtener la URL del portapapeles
        if self.starts_with_http(url):
            self.url_listbox.insert(tk.END, url)
        else:
            messagebox.showerror("Error", "El contenido del portapapeles no es una URL válida")

    def clean_urls(self):
        self.url_listbox.delete(0, tk.END)

    def clean_completed_downloads(self):
        for url, (progress, percentage_label, frame) in list(self.downloads.items()):
            if progress.get() == 100:
                frame.destroy()
                del self.downloads[url]

    def open_download_options(self):
        download_folder = filedialog.askdirectory()
        if not download_folder:
            messagebox.showerror("Error", "Selecciona un folder")
            return

        options_window = tk.Toplevel(self.root)
        options_window.title("Opciones de Descarga")
        options_window.config(bg="#e0e0e0")

        tk.Label(options_window, text="Formato:", bg="#e0e0e0").grid(row=0, column=0, padx=10, pady=10)
        format_var = tk.StringVar(value="mp3")
        
        format_frame = tk.Frame(options_window, bg="#e0e0e0")
        format_frame.grid(row=0, column=1, columnspan=3, padx=10, pady=10)
        tk.Radiobutton(format_frame, text="MP4", variable=format_var, value="mp4", bg="#e0e0e0", command=lambda: self.update_quality_options(format_var, options_window)).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(format_frame, text="MP3", variable=format_var, value="mp3", bg="#e0e0e0", command=lambda: self.update_quality_options(format_var, options_window)).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(format_frame, text="M4A", variable=format_var, value="m4a", bg="#e0e0e0", command=lambda: self.update_quality_options(format_var, options_window)).pack(side=tk.LEFT, padx=5)

        self.quality_frame = tk.Frame(options_window, bg="#e0e0e0")
        self.quality_frame.grid(row=1, column=0, columnspan=4, padx=10, pady=10)

        self.update_quality_options(format_var, options_window)

        tk.Button(options_window, text="Aceptar", command=lambda: self.start_download(download_folder, format_var.get(), self.quality_var.get(), self.audio_quality_var.get(), options_window)).grid(row=3, column=0, columnspan=4, pady=10)

    def update_quality_options(self, format_var, options_window):
        for widget in self.quality_frame.winfo_children():
            widget.destroy()

        if format_var.get() in ["mp4", "m4a"]:
            tk.Label(self.quality_frame, text="Calidad de Video:", bg="#e0e0e0").grid(row=0, column=0, padx=10, pady=10)
            self.quality_var = tk.StringVar(value="best")
            tk.Radiobutton(self.quality_frame, text="Mejor Calidad", variable=self.quality_var, value="best", bg="#e0e0e0").grid(row=0, column=1, padx=10, pady=10)
            tk.Radiobutton(self.quality_frame, text="1080p", variable=self.quality_var, value="1080p", bg="#e0e0e0").grid(row=0, column=2, padx=10, pady=10)
            tk.Radiobutton(self.quality_frame, text="720p", variable=self.quality_var, value="720p", bg="#e0e0e0").grid(row=0, column=3, padx=10, pady=10)
            tk.Radiobutton(self.quality_frame, text="480p", variable=self.quality_var, value="480p", bg="#e0e0e0").grid(row=0, column=4, padx=10, pady=10)
        else:
            tk.Label(self.quality_frame, text="Calidad de Audio:", bg="#e0e0e0").grid(row=0, column=0, padx=10, pady=10)
            self.audio_quality_var = tk.StringVar(value="192")
            tk.Radiobutton(self.quality_frame, text="320 kbps", variable=self.audio_quality_var, value="320", bg="#e0e0e0").grid(row=0, column=1, padx=10, pady=10)
            tk.Radiobutton(self.quality_frame, text="190 kbps", variable=self.audio_quality_var, value="190", bg="#e0e0e0").grid(row=0, column=2, padx=10, pady=10)
            tk.Radiobutton(self.quality_frame, text="128 kbps", variable=self.audio_quality_var, value="128", bg="#e0e0e0").grid(row=0, column=3, padx=10, pady=10)

    def start_download(self, download_folder, format, quality, audio_quality, options_window):
        options_window.destroy()
        urls = self.url_listbox.get(0, tk.END)
        if not urls:
            messagebox.showerror("Error", "No URL para descargar")
            return

        for url in urls:
            thread = threading.Thread(target=self.download_single_mp3, args=(url, download_folder, format, quality, audio_quality))
            thread.start()


    def download_single_mp3(self, url, download_folder, format, quality, audio_quality):
        try:
            if quality == "best":
                video_format = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo[ext=mp4]/best[ext=mp4]"
            elif quality == "1080p":
                video_format = "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080][ext=mp4]/best[height<=1080][ext=mp4]"
            elif quality == "720p":
                video_format = "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720][ext=mp4]/best[height<=720][ext=mp4]"
            elif quality == "480p":
                video_format = "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=480][ext=mp4]/best[height<=480][ext=mp4]"
            else:
                video_format = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo[ext=mp4]/best[ext=mp4]"

            ydl_opts = {
                'format': video_format if format == 'mp4' else 'bestaudio/best',
                'outtmpl': os.path.join(download_folder, '%(title)s.%(ext)s'),
                'ffmpeg_location': self.ffmpeg_location,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': format,
                    'preferredquality': audio_quality
                }] if format == 'mp3' else [],
                'progress_hooks': [self.progress_function],
                'keepvideo': False
            }
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                video_title = info_dict.get('title', None)
                file_path = ydl.prepare_filename(info_dict)
                self.downloaded_files[url] = file_path
                self.queue.put(('start', url, video_title))
                ydl.download([url])
                self.queue.put(('complete', url, video_title))

        except Exception as e:
            self.queue.put(("error", str(e)))

    def progress_function(self, d):
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded_bytes = d.get('downloaded_bytes')
            if total_bytes and downloaded_bytes:
                actual_percentage = downloaded_bytes / total_bytes * 100
                filename = d['filename']
                self.queue.put(('progress', filename, actual_percentage))

    def increment_progress(self):
        for url, (progress, percentage_label, frame) in list(self.downloads.items()):
            simulated_percentage = progress.get()
            if simulated_percentage < 95:  # Ajuste para no llegar al 100%
                increment = random.uniform(0.1, 0.4)  # Ajusta el rango para controlar la velocidad del incremento
                simulated_percentage += increment
                progress.set(min(simulated_percentage, 95))  # Asegúrate de no exceder el 95%
                percentage_label.config(text=f"{simulated_percentage:.2f}%")
        self.root.after(100, self.increment_progress)

    def update_queue(self):
        try:
            while True:
                msg = self.queue.get_nowait()
                if msg[0] == 'start':
                    url, video_title = msg[1], msg[2]
                    frame = tk.Frame(self.active_downloads_frame, bg="#e0e0e0")
                    frame.pack(fill=tk.X, padx=5, pady=5)
                    label = tk.Label(frame, text=video_title, anchor="w", width=60, bg="#e0e0e0", fg="black")
                    label.pack(side=tk.LEFT, padx=5)
                    progress = tk.DoubleVar()
                    progress_bar = ttk.Progressbar(frame, variable=progress, maximum=100)
                    progress_bar.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
                    percentage_label = tk.Label(frame, text="0%", width=5, bg="#e0e0e0", fg="black")
                    percentage_label.pack(side=tk.LEFT, padx=5)
                    self.downloads[url] = (progress, percentage_label, frame)
                elif msg[0] == 'complete':
                    filename = msg[1]
                    progress, percentage_label, frame = self.downloads.get(filename, (None, None, None))
                    if progress:
                        progress.set(100)
                        percentage_label.config(text="100%")
                        self.downloads[filename] = (progress, percentage_label, frame)
                    try:
                        original_file = self.downloaded_files.pop(filename)
                        # No eliminamos el archivo final convertido a MP4
                    except OSError as e:
                        print(f"Error al eliminar el archivo original: {e}")
                elif msg[0] == "error":
                    err_msg = msg[1]
                    messagebox.showerror("Error", err_msg)
        except queue.Empty:
            pass
        self.root.after(100, self.update_queue)

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeDownloaderApp(root)
    root.mainloop()
