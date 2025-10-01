import streamlit as st
import yt_dlp
import os

st.set_page_config(page_title="YouTube Playlist Downloader", layout="wide")
st.title("📥 YouTube Playlist Downloader")

# User inputs the playlist URL
playlist_url = st.text_input("Enter YouTube Playlist URL:")

# Optional: select format
format_choice = st.selectbox("Select download format:", ["mp4", "mp3"])

# Download button
if st.button("Download Playlist"):
    if not playlist_url:
        st.warning("Please enter a playlist URL!")
    else:
        download_dir = "downloads"
        try:
            os.makedirs(download_dir, exist_ok=True)
        except Exception as e:
            st.error(f"Failed to create download directory: {e}")
        
        st.info("Downloading playlist... This may take a few minutes.")

        # yt-dlp options
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
            'noplaylist': False,
            'progress_hooks': [
                lambda d: st.write(f"{d['_percent_str']} downloaded: {d.get('filename', '')}") 
                if d['status'] == 'downloading' else None
            ],
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
            with st.spinner("Downloading playlist..."):
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([playlist_url])
            st.success(f"✅ Download completed! Files saved in `{download_dir}` folder.")
            
            # Show list of downloaded files
            files = os.listdir(download_dir)
            if files:
                st.subheader("Downloaded files:")
                for f in files:
                    st.write(f"- {f}")
        except Exception as e:
            st.error(f"Error downloading playlist: {e}")
