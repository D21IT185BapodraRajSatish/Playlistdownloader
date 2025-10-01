import streamlit as st
import yt_dlp
import os
import zipfile
import tempfile
import shutil

st.set_page_config(page_title="YouTube Playlist Downloader", page_icon="🎵", layout="centered")

st.title("🎵 YouTube Playlist Downloader")

# Input field for playlist URL
playlist_url = st.text_input("Enter YouTube Playlist URL:")

# Format selection
format_choice = st.radio("Select download format:", ("Video (MP4)", "Audio (MP3)"))

# Download button
if st.button("Download Playlist") and playlist_url:
    with st.spinner("📥 Downloading playlist... Please wait ⏳"):

        # Temporary directory to store downloads
        temp_dir = tempfile.mkdtemp()
        output_template = os.path.join(temp_dir, "%(title)s.%(ext)s")

        # yt-dlp options
        if format_choice == "Video (MP4)":
            ydl_opts = {
                "outtmpl": output_template,
                "format": "bestvideo+bestaudio/best",
                "merge_output_format": "mp4",
                "ignoreerrors": True,
                "postprocessors": [{
                    "key": "FFmpegVideoConvertor",
                    "preferredformat": "mp4",  # force mp4 with audio
                }],
            }
        else:  # Audio MP3
            ydl_opts = {
                "outtmpl": output_template,
                "format": "bestaudio/best",
                "ignoreerrors": True,
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
