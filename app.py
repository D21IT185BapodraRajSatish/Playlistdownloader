import streamlit as st
import yt_dlp
import os
import zipfile
import tempfile
import shutil


st.set_page_config(page_title="YouTube Playlist Downloader", page_icon="🎵", layout="centered")
st.title("🎵 YouTube Playlist Downloader")

# Ensure yt-dlp is installed
try:
    import yt_dlp
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "git+https://github.com/yt-dlp/yt-dlp.git"])
    import yt_dlp

# Input field for playlist URL
playlist_url = st.text_input("Enter YouTube Playlist URL:")

# Format selection
format_choice = st.radio("Select download format:", ("Video (MP4)", "Audio (MP3)"))

# Quality options (only for video)
quality_choice = None
if format_choice == "Video (MP4)":
    quality_choice = st.selectbox(
        "Select Video Quality:",
        ("best", "1080p", "720p", "480p", "360p")
    )

# Placeholder for progress updates
progress_placeholder = st.empty()

# Download button
if st.button("Download Playlist") and playlist_url:
    with st.spinner("📥 Downloading playlist... Please wait ⏳"):

        # Temporary directory to store downloads
        temp_dir = tempfile.mkdtemp()
        output_template = os.path.join(temp_dir, "%(title)s.%(ext)s")

        # Progress hook
        def progress_hook(d):
            if d['status'] == 'downloading':
                percent = d.get('_percent_str', '0%')
                speed = d.get('_speed_str', '0 KB/s')
                eta = d.get('_eta_str', '00:00')
                progress_placeholder.text(
                    f"⬇️ Downloading: {percent} | Speed: {speed} | ETA: {eta}"
                )
            elif d['status'] == 'finished':
                progress_placeholder.text("✅ Download finished, processing...")

        # yt-dlp options
        if format_choice == "Video (MP4)":
            # Map quality to yt-dlp format string
            quality_map = {
                "best": "bestvideo+bestaudio/best",
                "1080p": "bestvideo[height<=1080]+bestaudio/best",
                "720p": "bestvideo[height<=720]+bestaudio/best",
                "480p": "bestvideo[height<=480]+bestaudio/best",
                "360p": "bestvideo[height<=360]+bestaudio/best",
            }
            ydl_opts = {
                "outtmpl": output_template,
                "format": quality_map[quality_choice],
                "merge_output_format": "mp4",
                "ignoreerrors": True,
                "progress_hooks": [progress_hook],
            }
        else:  # Audio MP3
            ydl_opts = {
                "outtmpl": output_template,
                "format": "bestaudio/best",
                "ignoreerrors": True,
                "progress_hooks": [progress_hook],
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            }

        # Download playlist
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([playlist_url])

        # Create ZIP file
        zip_path = os.path.join(temp_dir, "playlist.zip")
        with zipfile.ZipFile(zip_path, "w") as zipf:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    if file.endswith(".mp4") or file.endswith(".mp3"):
                        zipf.write(os.path.join(root, file), file)

        # Provide download button
        with open(zip_path, "rb") as f:
            st.download_button(
                label="📂 Download Playlist as ZIP",
                data=f,
                file_name="playlist.zip",
                mime="application/zip"
            )

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)
    st.success("✅ Playlist download completed!")
