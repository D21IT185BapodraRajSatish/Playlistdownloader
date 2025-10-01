import streamlit as st
import yt_dlp
import os

st.title("YouTube Playlist Downloader")

# User inputs the playlist URL
playlist_url = st.text_input("Enter YouTube Playlist URL:")

# Optional: select format
format_choice = st.selectbox("Select download format:", ["mp4", "mp3"])

# Download button
if st.button("Download Playlist"):
    if not playlist_url:
        st.warning("Please enter a playlist URL!")
    else:
        # Create download folder
        download_dir = "downloads"
        os.makedirs(download_dir, exist_ok=True)
        
        st.info("Downloading playlist...")
        
        # yt-dlp options
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
            'noplaylist': False,
        }
        if format_choice == "mp3":
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([playlist_url])
            st.success(f"Download completed! Files saved in `{download_dir}` folder.")
        except Exception as e:
            st.error(f"Error downloading playlist: {e}")
