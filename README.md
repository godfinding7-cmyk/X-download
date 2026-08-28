# TweetSave — Working X/Twitter Video & GIF Downloader

This version uses a Python/Flask backend with yt-dlp. It does not depend on an unrestricted public Cobalt API.

## Local setup
1. Install Python 3.10+.
2. Open a terminal in this folder.
3. Run: `pip install -r requirements.txt`
4. Run: `python run.py`
5. Open: `http://localhost:5000`

## Docker
Build:
`docker build -t tweetsave .`

Run:
`docker run -p 5000:5000 tweetsave`

Then open `http://localhost:5000`.

## Optional X cookies
X sometimes requires logged-in cookies even for content that appears public. Export Netscape-format cookies to a file on your server and set:
`YTDLP_COOKIES_FILE=/app/cookies.txt`

Never expose the cookies file publicly.

## Deployment
Deploy the Docker image or Python app to any host that supports long-running Python processes / Docker, such as a VPS or suitable container host.

## Use responsibly
Only download public media you have permission to save or use. Private/restricted posts are not supported.
