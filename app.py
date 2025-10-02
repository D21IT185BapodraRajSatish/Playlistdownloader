import streamlit as st
import yt_dlp
import os
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

st.set_page_config(page_title="YouTube Playlist Downloader", layout="wide")
st.title("📥 YouTube Playlist Downloader")

# Initialize session state
if 'all_videos' not in st.session_state:
    st.session_state['all_videos'] = []
if 'checkbox_states' not in st.session_state:
    st.session_state['checkbox_states'] = {}
if 'last_playlist_url' not in st.session_state:
    st.session_state['last_playlist_url'] = ""

MAX_WORKERS = 3  # Parallel video info fetching


def format_duration(seconds):
    """Convert seconds to MM:SS format"""
    if not seconds:
        return "N/A"
    mins, secs = divmod(int(seconds), 60)
    return f"{mins}:{secs:02d}"


def fetch_video_info(entry):
    """Fetch detailed info for a single video"""
    if not entry or not entry.get('id'):
        return None
    
    video_url = f"https://www.youtube.com/watch?v={entry['id']}"
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            vid_info = ydl.extract_info(video_url, download=False)
        
        return {
            "title": vid_info.get("title", "Unknown Title"),
            "id": vid_info.get("id"),
            "thumbnail": vid_info.get("thumbnail"),
            "url": video_url,
            "duration": vid_info.get("duration"),
            "duration_str": format_duration(vid_info.get("duration"))
        }
    except Exception:
        st.warning(f"⚠️ Could not fetch: {entry.get('title', entry.get('id', 'Unknown'))}")
        return None


# Playlist input
playlist_url = st.text_input(
    "Enter YouTube Playlist URL:",
    placeholder="https://www.youtube.com/playlist?list=..."
)

col1, col2 = st.columns(2)
with col1:
    format_choice = st.selectbox("Format:", ["mp4", "mp3"])
with col2:
    if format_choice == "mp4":
        quality_choice = st.selectbox(
            "Quality:",
            ["best", "1080p", "720p", "480p", "360p"]
        )
    else:
        quality_choice = None
        st.selectbox("Audio Quality:", ["192 kbps"], disabled=True)


# Fetch playlist
if st.button("🔍 Fetch Playlist", type="primary", use_container_width=True):
    url = playlist_url.strip()
    
    if url == st.session_state['last_playlist_url'] and st.session_state['all_videos']:
        st.info("✅ Playlist already loaded! Select videos below.")
    elif not url:
        st.warning("⚠️ Please enter a playlist URL!")
    else:
        st.session_state['all_videos'] = []
        st.session_state['checkbox_states'] = {}
        st.session_state['last_playlist_url'] = url
        
        try:
            with st.spinner("🔄 Fetching playlist information..."):
                ydl_opts = {
                    'extract_flat': 'in_playlist',
                    'quiet': True,
                    'no_warnings': True
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                
                if 'entries' in info and info['entries']:
                    entries = [e for e in info['entries'] if e]
                    total_videos = len(entries)
                    
                    st.info(f"📊 Found {total_videos} videos. Fetching details...")
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                        future_to_entry = {executor.submit(fetch_video_info, entry): entry for entry in entries}
                        
                        completed = 0
                        for future in as_completed(future_to_entry):
                            video_obj = future.result()
                            if video_obj:
                                st.session_state['all_videos'].append(video_obj)
                                st.session_state['checkbox_states'][video_obj['id']] = False
                            
                            completed += 1
                            progress_bar.progress(completed / total_videos)
                            status_text.text(f"Loading... {completed}/{total_videos}")
                    
                    progress_bar.empty()
                    status_text.empty()
                    st.success(f"✅ Loaded {len(st.session_state['all_videos'])} videos!")
                else:
                    st.error("❌ No videos found in this playlist.")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.session_state['last_playlist_url'] = ""


# Video selection
if st.session_state['all_videos']:
    num_videos = len(st.session_state['all_videos'])
    st.divider()
    st.subheader(f"📹 Select Videos ({num_videos} available)")

    # Selection controls
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        if st.button("✅ Select All", key="select_all_btn"):
            for v in st.session_state['all_videos']:
                st.session_state['checkbox_states'][v['id']] = True
                st.session_state[f"chk_{v['id']}"] = True
            st.rerun()
    with col2:
        if st.button("❌ Clear All", key="clear_all_btn"):
            for v in st.session_state['all_videos']:
                st.session_state['checkbox_states'][v['id']] = False
                st.session_state[f"chk_{v['id']}"] = False
            st.rerun()

    selected_videos_for_download = []
    for video in st.session_state['all_videos']:
        col1, col2 = st.columns([1, 5])
        with col1:
            if video["thumbnail"]:
                st.image(video["thumbnail"], width=120)
        with col2:
            checked = st.checkbox(
                f"**{video['title']}**  \n⏱️ {video['duration_str']}",
                key=f"chk_{video['id']}",
                value=st.session_state['checkbox_states'].get(video['id'], False)
            )
            st.session_state['checkbox_states'][video['id']] = checked
            if checked:
                selected_videos_for_download.append(video)

    st.divider()
    
    selected_count = len(selected_videos_for_download)
    st.caption(f"✅ {selected_count} selected for download")

    # Download mode option
    download_mode = st.radio("Download Mode:", ["Selected Videos", "Complete Playlist"])

    if st.button("⬇️ Start Download", type="primary", use_container_width=True):
        with tempfile.TemporaryDirectory() as tmpdir:
            progress_bar = st.progress(0)
            progress_text = st.empty()
            current_status = st.empty()
            download_progress = st.empty()

            def progress_hook(d):
                if d['status'] == 'downloading':
                    percent = d.get('_percent_str', '0%')
                    speed = d.get('_speed_str', 'N/A')
                    eta = d.get('_eta_str', 'N/A')
                    download_progress.markdown(
                        f"**Progress:** {percent} | **Speed:** {speed} | **ETA:** {eta}"
                    )
                elif d['status'] == 'finished':
                    download_progress.success("✅ File finished downloading")

            # yt-dlp options
            if format_choice == "mp3":
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': os.path.join(tmpdir, '%(title)s.%(ext)s'),
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'progress_hooks': [progress_hook],
                    'ignoreerrors': True,
                }
            else:
                quality_map = {
                    "1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                    "720p": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                    "480p": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                    "360p": "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                    "best": "best[ext=mp4]/best"
                }
                ydl_opts = {
                    'format': quality_map.get(quality_choice, 'best'),
                    'outtmpl': os.path.join(tmpdir, '%(title)s.%(ext)s'),
                    'progress_hooks': [progress_hook],
                    'ignoreerrors': True,
                    'merge_output_format': 'mp4'
                }

            # Choose what to download
            urls_to_download = []
            if download_mode == "Selected Videos":
                urls_to_download = [v["url"] for v in selected_videos_for_download]
            else:
                urls_to_download = [v["url"] for v in st.session_state['all_videos']]

            if not urls_to_download:
                st.warning("⚠️ Nothing to download.")
            else:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    for idx, url in enumerate(urls_to_download):
                        current_status.info(f"📥 Downloading {idx+1}/{len(urls_to_download)}")
                        try:
                            ydl.download([url])
                        except Exception as e:
                            st.error(f"❌ Failed: {str(e)}")
                        progress_bar.progress((idx + 1) / len(urls_to_download))

                # Create ZIP in temp dir
                zip_path = shutil.make_archive(
                    os.path.join(tmpdir, "playlist_downloads"), 'zip', tmpdir
                )
                with open(zip_path, "rb") as fz:
                    st.download_button(
                        label="📦 Download All as ZIP",
                        data=fz,
                        file_name="playlist_downloads.zip",
                        mime="application/zip",
                        type="primary"
                    )
