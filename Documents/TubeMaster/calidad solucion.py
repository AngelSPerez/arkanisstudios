import os
import sys
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import yt_dlp as youtube_dl
import threading

class YouTubeDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TubeMaster23")
        self.root.config(bg="#e0e0e0")
        self.queue = queue.Queue()
        self.create_widgets()
        self.update_queue()
        self.downloads = {}
        self.downloaded_files = {}

        # Definir la ubicación de ffmpeg en la misma carpeta que el script en ejecución
        self.ffmpeg_location = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ffmpeg.exe')

        if not os.path.isfile(self.ffmpeg_location):
            print(f"WARNING: ffmpeg-location {self.ffmpeg_location} does not exist! Continuing without ffmpeg")
        else:
            print(f"ffmpeg found at {self.ffmpeg_location}")

    def open_download_options(self):
        download_folder = filedialog.askdirectory()
        if not download_folder:
            messagebox.showerror("Error", "Selecciona un folder")
            return

        options_window = tk.Toplevel(self.root)
        options_window.title("Opciones de Descarga")
        options_window.config(bg="#e0e0e0")

        tk.Label(options_window, text="Formato de Descarga:", bg="#e0e0e0").grid(row=0, column=0, padx=10, pady=10)
        format_var = tk.StringVar(value="mp3")
        tk.Radiobutton(options_window, text="MP3", variable=format_var, value="mp3", bg="#e0e0e0").grid(row=0, column=1, padx=10, pady=10)
        tk.Radiobutton(options_window, text="MP4", variable=format_var, value="mp4", bg="#e0e0e0").grid(row=0, column=2, padx=10, pady=10)

        tk.Label(options_window, text="Calidad de Video:", bg="#e0e0e0").grid(row=1, column=0, padx=10, pady=10)
        quality_var = tk.StringVar(value="best")
        tk.Radiobutton(options_window, text="Mejor", variable=quality_var, value="best", bg="#e0e0e0").grid(row=1, column=1, padx=10, pady=10)
        tk.Radiobutton(options_window, text="Media", variable=quality_var, value="medium", bg="#e0e0e0").grid(row=1, column=2, padx=10, pady=10)
        tk.Radiobutton(options_window, text="Baja", variable=quality_var, value="worst", bg="#e0e0e0").grid(row=1, column=3, padx=10, pady=10)

        tk.Button(options_window, text="Aceptar", command=lambda: self.start_download(download_folder, format_var.get(), quality_var.get())).grid(row=2, column=0, columnspan=3, pady=10)

    def start_download(self, download_folder, format, quality):
        urls = self.url_listbox.get(0, tk.END)
        if not urls:
            messagebox.showerror("Error", "No URL para descargar")
            return

        for url in urls:
            thread = threading.Thread(target=self.download_single_mp3, args=(url, download_folder, format, quality))
            thread.start()

    def download_single_mp3(self, url, download_folder, format, quality):
        try:
            ydl_opts = {
                'format': f'bestvideo[ext={format}][height<=?{self.get_video_quality(quality)}]+bestaudio/best[ext={format}]' if format == 'mp4' else f'bestaudio/best[ext={format}]',
                'outtmpl': os.path.join(download_folder, '%(title)s.%(ext)s'),
                'ffmpeg_location': self.ffmpeg_location,
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': format, 'preferredquality': '192'}] if format == 'mp3' else [],
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

    def get_video_quality(self, quality):
        if quality == 'best':
            return '1080'
        elif quality == 'medium':
            return '720'
        elif quality == 'worst':
            return '480'
        else:
            return '1080'

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
                elif msg[0] == 'progress':
                    filename, percentage = msg[1], msg[2]
                    progress, percentage_label, frame = self.downloads.get(filename, (None, None, None))
                    if progress:
                        progress.set(percentage)
                        percentage_label.config(text=f"{percentage:.2f}%")
                elif msg[0] == 'complete':
                    filename = msg[1]
                    progress, percentage_label, frame = self.downloads.get(filename, (None, None, None))
                    if progress:
                        progress.set(100)
                        percentage_label.config(text="100%")
                        self.downloads[filename] = (progress, percentage_label, frame)
                    try:
                        original_file = self.downloaded_files.pop(filename)
                        if os.path.isfile(original_file):
                            os.remove(original_file)
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
