#!/usr/bin/env python3
from flask import Flask, request, send_file, abort, jsonify
import yt_dlp
import os

app = Flask(__name__)


@app.route("/download")
def download_audio():
    video_id = request.args.get("id")
    if not video_id:
        return abort(400, "Missing `id` parameter")

    url = f"https://www.youtube.com/watch?v={video_id}"
    # Path where you've placed the ffmpeg & ffprobe binaries
    ffmpeg_path = "/opt/homebrew/bin"  # Homebrew’s install prefix on Apple Silicon

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'/tmp/{video_id}.%(ext)s',
        'ffmpeg_location': ffmpeg_path,         # <-- add this
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info).rsplit('.', 1)[0] + '.mp3'
    except Exception as e:
        return abort(500, f"Conversion failed: {e}")

    if os.path.exists(filename):
        return send_file(filename, as_attachment=True)
    else:
        return abort(500, "MP3 file not found after conversion")


from flask import url_for

@app.route("/info")
def video_info():
    video_id = request.args.get("id")
    if not video_id:
        return abort(400, "Missing `id` parameter")

    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = { 'quiet': True, 'skip_download': True }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title    = info.get("title")     or video_id
            thumb    = info.get("thumbnail") or ""
            # Build the local URLs for audio & cover
            audio_url = url_for('download_audio', id=video_id, _external=True)
            cover_url = thumb

            return jsonify({
                "id":       video_id,
                "title":    title,
                "audioUrl": audio_url,
                "coverUrl": cover_url
            })
    except Exception as e:
        return abort(500, f"Metadata fetch failed: {e}")

# Run as before…

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
