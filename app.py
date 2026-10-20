import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

def get_ffmpeg_path():
    # 1. Check if running inside PyInstaller bundle
    if getattr(sys, 'frozen', False):
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        try:
            for fname in os.listdir(base_dir):
                if fname.lower().startswith("ffmpeg") and fname.lower().endswith(".exe"):
                    return os.path.join(base_dir, fname)
        except Exception:
            pass
        exe_dir = os.path.dirname(sys.executable)
        try:
            for fname in os.listdir(exe_dir):
                if fname.lower().startswith("ffmpeg") and fname.lower().endswith(".exe"):
                    return os.path.join(exe_dir, fname)
        except Exception:
            pass

    # 2. Check imageio_ffmpeg
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.exists(exe):
            return exe
    except Exception:
        pass

    # 3. Check system PATH
    import shutil
    which_ffmpeg = shutil.which("ffmpeg")
    if which_ffmpeg:
        return which_ffmpeg
    return None

FFMPEG_PATH = get_ffmpeg_path()

def get_default_output_dir():
    # If D: exists, prefer D:\mini
    if os.path.exists("D:\\"):
        d_dir = r"D:\mini"
        try:
            os.makedirs(d_dir, exist_ok=True)
            return d_dir
        except Exception:
            pass
    # Otherwise fallback to user's standard Downloads folder
    user_downloads = os.path.join(os.path.expanduser("~"), "Downloads", "YouTubeDownloads")
    os.makedirs(user_downloads, exist_ok=True)
    return user_downloads

DEFAULT_OUTPUT_DIR = get_default_output_dir()

class YouTubeDownloaderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Video & Audio Downloader")
        self.geometry("660x560")
        self.minsize(580, 500)

        # Style configuration
        self.style = ttk.Style(self)
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")

        self.style.configure("TLabel", font=("Segoe UI", 10))
        self.style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6)
        self.style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"))
        self.style.configure("Status.TLabel", font=("Segoe UI", 9))

        self.is_downloading = False
        self._build_ui()

    def _build_ui(self):
        container = ttk.Frame(self, padding=20)
        container.pack(fill=tk.BOTH, expand=True)

        # Title
        title_lbl = ttk.Label(container, text="🎬 YouTube Downloader", style="Header.TLabel")
        title_lbl.pack(anchor="w", pady=(0, 15))

        # URL Input
        url_frame = ttk.LabelFrame(container, text="YouTube URL", padding=10)
        url_frame.pack(fill=tk.X, pady=(0, 12))

        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(url_frame, textvariable=self.url_var, font=("Segoe UI", 10))
        self.url_entry.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=(0, 8))

        clear_btn = ttk.Button(url_frame, text="Paste", width=7, command=self._paste_clipboard)
        clear_btn.pack(side=tk.RIGHT)

        # Save Directory
        dir_frame = ttk.LabelFrame(container, text="Save Folder", padding=10)
        dir_frame.pack(fill=tk.X, pady=(0, 12))

        self.dir_var = tk.StringVar(value=DEFAULT_OUTPUT_DIR)
        dir_entry = ttk.Entry(dir_frame, textvariable=self.dir_var, font=("Segoe UI", 9))
        dir_entry.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=(0, 8))

        browse_btn = ttk.Button(dir_frame, text="Browse...", width=9, command=self._browse_dir)
        browse_btn.pack(side=tk.RIGHT)

        # Format & Quality Options
        opts_frame = ttk.LabelFrame(container, text="Download Options", padding=10)
        opts_frame.pack(fill=tk.X, pady=(0, 15))

        # Media Type Radio Buttons
        self.type_var = tk.StringVar(value="video")
        r_vid = ttk.Radiobutton(
            opts_frame, text="Video (MP4)", value="video",
            variable=self.type_var, command=self._toggle_options_state
        )
        r_vid.grid(row=0, column=0, padx=(0, 15), sticky="w")

        r_aud = ttk.Radiobutton(
            opts_frame, text="Âm thanh (Audio)", value="audio",
            variable=self.type_var, command=self._toggle_options_state
        )
        r_aud.grid(row=0, column=1, padx=(0, 20), sticky="w")

        # Quality / Format Dropdown
        self.opt_label = ttk.Label(opts_frame, text="Độ phân giải:")
        self.opt_label.grid(row=0, column=2, padx=(10, 5), sticky="e")

        self.quality_var = tk.StringVar(value="Best (Tốt nhất có sẵn - 4K/2K/1080p)")
        self.quality_combo = ttk.Combobox(
            opts_frame,
            textvariable=self.quality_var,
            values=[
                "Best (Tốt nhất có sẵn - 4K/2K/1080p)",
                "4K (2160p)",
                "2K (1440p)",
                "Full HD (1080p)",
                "HD (720p)",
                "SD (480p)",
                "Low (360p)"
            ],
            state="readonly",
            width=28
        )
        self.quality_combo.grid(row=0, column=3, sticky="w")

        # Row 1: Anti-403 bypass & Cookie options
        self.bypass_403_var = tk.BooleanVar(value=True)
        self.bypass_chk = ttk.Checkbutton(
            opts_frame,
            text="Chống 403 (iOS/Android)",
            variable=self.bypass_403_var
        )
        self.bypass_chk.grid(row=1, column=0, columnspan=2, sticky="w", pady=(10, 0))

        cookie_lbl = ttk.Label(opts_frame, text="Cookie trình duyệt:")
        cookie_lbl.grid(row=1, column=2, padx=(10, 5), sticky="e", pady=(10, 0))

        self.cookie_var = tk.StringVar(value="Không dùng")
        self.cookie_combo = ttk.Combobox(
            opts_frame,
            textvariable=self.cookie_var,
            values=[
                "Không dùng",
                "edge",
                "chrome",
                "firefox",
                "brave"
            ],
            state="readonly",
            width=28
        )
        self.cookie_combo.grid(row=1, column=3, sticky="w", pady=(10, 0))

        # Action Buttons
        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill=tk.X, pady=(0, 15))

        self.dl_btn = ttk.Button(btn_frame, text="⬇ Start Download", command=self._start_download_thread)
        self.dl_btn.pack(side=tk.LEFT, padx=(0, 10))

        open_folder_btn = ttk.Button(btn_frame, text="📁 Open Folder", command=self._open_folder)
        open_folder_btn.pack(side=tk.LEFT)

        # Progress bar
        self.progress_bar = ttk.Progressbar(container, mode="determinate", maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(0, 8))

        # Status text
        self.status_var = tk.StringVar(value="Ready. Target directory: D:\\mini")
        self.status_lbl = ttk.Label(container, textvariable=self.status_var, style="Status.TLabel", foreground="#333333")
        self.status_lbl.pack(anchor="w", pady=(0, 8))

        # Log box
        log_frame = ttk.LabelFrame(container, text="Log", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(log_frame, height=8, font=("Consolas", 9), wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _paste_clipboard(self):
        try:
            clipboard = self.clipboard_get().strip()
            self.url_var.set(clipboard)
        except Exception:
            pass

    def _browse_dir(self):
        chosen = filedialog.askdirectory(initialdir=self.dir_var.get())
        if chosen:
            self.dir_var.set(chosen)

    def _toggle_options_state(self):
        if self.type_var.get() == "video":
            self.opt_label.config(text="Độ phân giải:")
            self.quality_combo.config(
                values=[
                    "Best (Tốt nhất có sẵn - 4K/2K/1080p)",
                    "4K (2160p)",
                    "2K (1440p)",
                    "Full HD (1080p)",
                    "HD (720p)",
                    "SD (480p)",
                    "Low (360p)"
                ],
                state="readonly"
            )
            self.quality_var.set("Best (Tốt nhất có sẵn - 4K/2K/1080p)")
        else:
            self.opt_label.config(text="Định dạng âm thanh:")
            self.quality_combo.config(
                values=[
                    "MP4 Audio (m4a/aac - Gốc cao nhất)",
                    "MP3 Audio (320kbps - Cực nét)",
                    "MP3 Audio (192kbps - Chuẩn)"
                ],
                state="readonly"
            )
            self.quality_var.set("MP4 Audio (m4a/aac - Gốc cao nhất)")

    def _open_folder(self):
        folder = self.dir_var.get()
        if os.path.exists(folder):
            os.startfile(folder)
        else:
            messagebox.showwarning("Notice", f"Directory {folder} does not exist yet.")

    def log(self, message: str):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def _progress_hook(self, d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes') or 0
            if total > 0:
                percent = (downloaded / total) * 100
                self.progress_bar['value'] = percent
                speed_str = d.get('_speed_str', 'N/A')
                eta_str = d.get('_eta_str', 'N/A')
                self.status_var.set(f"Downloading: {percent:.1f}% ({speed_str}, ETA: {eta_str})")
            else:
                self.status_var.set("Downloading...")
        elif d['status'] == 'finished':
            self.progress_bar['value'] = 100
            self.status_var.set("Download complete! Finalizing / Converting...")
            self.log("[Finished downloading stream, processing...]")

    def _start_download_thread(self):
        if self.is_downloading:
            messagebox.showinfo("In Progress", "A download is already running!")
            return

        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Empty URL", "Please enter a valid YouTube URL.")
            return

        save_dir = self.dir_var.get().strip()
        if not save_dir:
            save_dir = DEFAULT_OUTPUT_DIR
            self.dir_var.set(save_dir)

        os.makedirs(save_dir, exist_ok=True)

        self.is_downloading = True
        self.dl_btn.config(state="disabled")
        self.progress_bar['value'] = 0
        self.status_var.set("Starting download...")
        self.log(f"--- Starting task for: {url} ---")

        thread = threading.Thread(
            target=self._run_download,
            args=(url, save_dir, self.type_var.get(), self.quality_var.get()),
            daemon=True
        )
        thread.start()

    def _run_download(self, url, save_dir, media_type, quality):
        outtmpl = os.path.join(save_dir, "%(title)s.%(ext)s")
        ydl_opts = {
            'outtmpl': outtmpl,
            'progress_hooks': [self._progress_hook],
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'quiet': False,
            'no_warnings': False,
            'socket_timeout': 30,
            'retries': 15,
            'fragment_retries': 15,
            'file_access_retries': 5,
            'retry_sleep_functions': {'http': lambda n: 2 * n},
        }

        # 1. Anti-403 bypass: Prioritize iOS / Android / mweb clients without desktop User-Agent conflict
        if self.bypass_403_var.get():
            ydl_opts['extractor_args'] = {
                'youtube': {
                    'player_client': ['ios', 'android', 'mweb']
                }
            }

        # 2. Browser cookies to bypass IP bot-check or required sign-in
        cookie_val = self.cookie_var.get().strip().lower()
        if cookie_val and cookie_val not in ("không dùng", "none"):
            ydl_opts['cookiesfrombrowser'] = (cookie_val, )

        if FFMPEG_PATH and os.path.exists(FFMPEG_PATH):
            ydl_opts['ffmpeg_location'] = FFMPEG_PATH

        if media_type == "audio":
            if "MP4" in quality or "m4a" in quality.lower():
                ydl_opts['format'] = 'ba[ext=m4a]/ba/bestaudio'
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'm4a',
                }]
            else:
                bitrate = '320' if '320' in quality else '192'
                ydl_opts['format'] = 'bestaudio/best'
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': bitrate,
                }]
        else:
            # Video mode - Enhanced selection
            if "4K" in quality or "2160p" in quality:
                ydl_opts['format'] = 'bestvideo[height<=2160]+bestaudio/best[height<=2160]/best'
            elif "2K" in quality or "1440p" in quality:
                ydl_opts['format'] = 'bestvideo[height<=1440]+bestaudio/best[height<=1440]/best'
            elif "1080p" in quality:
                ydl_opts['format'] = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best'
            elif "720p" in quality:
                ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best[height<=720]/best'
            elif "480p" in quality:
                ydl_opts['format'] = 'bestvideo[height<=480]+bestaudio/best[height<=480]/best'
            elif "360p" in quality:
                ydl_opts['format'] = 'bestvideo[height<=360]+bestaudio/best[height<=360]/best'
            else:
                # Absolute Best Quality: highest resolution & highest bitrate available
                ydl_opts['format'] = 'bestvideo*+bestaudio/best'

            ydl_opts['merge_output_format'] = 'mp4'

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'Media')
                self.log(f"Successfully downloaded: {title}")

            self.status_var.set("Complete! Saved to " + save_dir)
            messagebox.showinfo("Success", f"Download finished successfully!\nSaved to: {save_dir}")
        except Exception as e:
            err_msg = str(e)
            self.log(f"Error: {err_msg}")
            if "403" in err_msg or "forbidden" in err_msg.lower() or "bot" in err_msg.lower():
                self.log("💡 GỢI Ý: Lỗi 403 / Chặn Bot từ YouTube. Bạn hãy thử chọn 'Cookie trình duyệt' (ví dụ: edge hoặc chrome) ở phần Tùy chọn rồi tải lại.")
            self.status_var.set("Download failed. See log.")
            messagebox.showerror("Download Error", f"An error occurred:\n{err_msg}")
        finally:
            self.is_downloading = False
            self.dl_btn.config(state="normal")

if __name__ == "__main__":
    if yt_dlp is None:
        print("yt-dlp is required. Please install it using: pip install yt-dlp")
        sys.exit(1)
    app = YouTubeDownloaderApp()
    app.mainloop()
