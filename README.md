# YouTube Downloader

Ung dung desktop viet bang Python va Tkinter de tai video hoac am thanh tu YouTube.

## Tinh nang

- Tai video theo do phan giai tu 360p den 4K.
- Tai am thanh va chuyen sang MP3.
- Chon thu muc luu file.
- Ho tro FFmpeg thong qua `imageio-ffmpeg` hoac FFmpeg trong PATH.
- Ho tro cookie trinh duyet va tuy chon xu ly loi 403.

## Yeu cau

- Windows
- Python 3.9 tro len
- Cac goi Python:

```bat
pip install yt-dlp imageio-ffmpeg
```

## Chay tu ma nguon

```bat
python app.py
```

Hoac nhap dup vao `run.bat`.

## Build file EXE

Cai PyInstaller neu may chua co:

```bat
pip install pyinstaller
```

Build theo file spec:

```bat
pyinstaller YouTubeDownloader.spec
```

File thuc thi se duoc tao trong thu muc `dist/`.

## Luu y

- Mac dinh ung dung uu tien luu file vao `D:\\mini` neu o dia D ton tai.
- Neu khong co o dia D, file se duoc luu vao `Downloads\\YouTubeDownloads`.
- Chi tai noi dung ma ban co quyen su dung va tuan thu dieu khoan cua YouTube.
