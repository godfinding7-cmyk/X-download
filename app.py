from flask import Flask, request, jsonify, send_from_directory
from urllib.parse import urlparse
import yt_dlp
import os

app = Flask(__name__, static_folder='static', static_url_path='')

ALLOWED_HOSTS = {'x.com', 'www.x.com', 'twitter.com', 'www.twitter.com', 'mobile.twitter.com'}

def valid_x_url(value: str) -> bool:
    try:
        p = urlparse(value)
        return p.scheme in ('http', 'https') and p.netloc.lower() in ALLOWED_HOSTS and '/status/' in p.path
    except Exception:
        return False

@app.get('/')
def home():
    return send_from_directory(app.static_folder, 'index.html')

@app.post('/api/twitter')
def twitter_media():
    body = request.get_json(silent=True) or {}
    url = str(body.get('url', '')).strip()

    if not valid_x_url(url):
        return jsonify(error='Invalid X/Twitter post URL.'), 400

    opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'noplaylist': True,
        'format': 'best',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36'
        }
    }

    cookies = os.environ.get('YTDLP_COOKIES_FILE')
    if cookies:
        opts['cookiefile'] = cookies

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)

        # Some extractors may wrap a single post in entries.
        if info and info.get('entries'):
            entries = [e for e in info.get('entries') if e]
            if entries:
                info = entries[0]

        formats = info.get('formats') or []
        candidates = []
        seen = set()

        for f in formats:
            media_url = f.get('url')
            if not media_url or media_url in seen:
                continue
            seen.add(media_url)

            # Prefer actual video formats. GIF posts on X are typically served as MP4.
            vcodec = f.get('vcodec')
            if vcodec == 'none':
                continue

            height = f.get('height')
            width = f.get('width')
            ext = (f.get('ext') or 'mp4').upper()
            quality = f'{height}p' if height else (f.get('format_note') or f.get('format') or 'Video')
            candidates.append({
                'quality': quality,
                'url': media_url,
                'ext': ext,
                '_height': height or 0,
                '_width': width or 0,
                '_tbr': f.get('tbr') or 0
            })

        # Best quality first, limit duplicate-looking entries.
        candidates.sort(key=lambda x: (x['_height'], x['_width'], x['_tbr']), reverse=True)
        output = []
        labels = set()
        for item in candidates:
            label = item['quality']
            if label in labels and len(output) >= 1:
                continue
            labels.add(label)
            item.pop('_height', None); item.pop('_width', None); item.pop('_tbr', None)
            output.append(item)
            if len(output) >= 6:
                break

        # Fallback to yt-dlp's chosen direct URL if formats are absent.
        if not output and info.get('url'):
            output.append({
                'quality': f"{info.get('height')}p" if info.get('height') else 'Best quality',
                'url': info['url'],
                'ext': (info.get('ext') or 'mp4').upper()
            })

        if not output:
            return jsonify(error='No downloadable video or GIF was found in this public post.'), 404

        title = info.get('title') or info.get('description') or 'X / Twitter media'
        if len(title) > 100:
            title = title[:97] + '...'

        return jsonify({
            'title': title,
            'thumbnail': info.get('thumbnail') or '',
            'media': output
        })

    except yt_dlp.utils.DownloadError as e:
        msg = str(e)
        if 'cookies' in msg.lower() or 'login' in msg.lower():
            return jsonify(error='X requires authentication for this post. Add a cookies file on the server and try again.'), 422
        return jsonify(error='Could not read this public X post. It may be unavailable, restricted, or X may have changed access rules.'), 502
    except Exception:
        return jsonify(error='Server could not process this post.'), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
