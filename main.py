from fastapi import FastAPI, HTTPException 
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import URL
from base62 import encode
import validators
import redis
from fastapi.responses import HTMLResponse
import os
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


# Create tables
Base.metadata.create_all(bind=engine)

# Initialize app
app = FastAPI()

# Redis setup
r = redis.Redis(host='localhost', port=6379, db=0)


# -----------------------------
# 🔗 SHORTEN URL API
# -----------------------------
@app.post("/shorten")
def shorten_url(request: dict):
    db: Session = SessionLocal()

    long_url = request.get("url")
    custom_code = request.get("custom_code")

    # ✅ Validate URL
    if not validators.url(long_url):
        raise HTTPException(status_code=400, detail="Invalid URL")

    # ✅ Custom Alias Logic
    if custom_code:
        existing = db.query(URL).filter(URL.short_code == custom_code).first()
        if existing:
            raise HTTPException(status_code=400, detail="Custom code already exists")

        new_url = URL(long_url=long_url, short_code=custom_code)
        db.add(new_url)
        db.commit()

        return {"short_url": f"http://localhost:8000/{custom_code}"}

    # ✅ Default Base62 Flow
    new_url = URL(long_url=long_url)
    db.add(new_url)
    db.commit()
    db.refresh(new_url)

    short_code = encode(new_url.id)

    new_url.short_code = short_code
    db.commit()

    return {"short_url": f"{BASE_URL}/{short_code}"}


# -----------------------------
#  REDIRECT API
# -----------------------------

@app.get("/{short_code}")
def redirect(short_code: str):
    db: Session = SessionLocal()

    cached_url = None

    # ✅ Safe Redis check
    try:
        cached_url = r.get(short_code)
    except:
        cached_url = None

    # ✅ ALWAYS update click count (important)
    url = db.query(URL).filter(URL.short_code == short_code).first()

    if not url:
        raise HTTPException(status_code=404, detail="URL not found")

    url.click_count += 1
    db.commit()

    # ✅ If cache exists → use it
    if cached_url:
        return RedirectResponse(url=cached_url.decode(), status_code=302)

    # ❗ Else fallback to DB
    try:
        r.set(short_code, url.long_url)
    except:
        pass

    return RedirectResponse(url=url.long_url, status_code=302)

    # ❗ DB lookup
    url = db.query(URL).filter(URL.short_code == short_code).first()

    if not url:
        raise HTTPException(status_code=404, detail="URL not found")

    # ✅ cache it
    try:
        r.set(short_code, url.long_url)
    except:
        pass

    # ✅ increment count
    url.click_count += 1
    db.commit()

    return RedirectResponse(url=url.long_url, status_code=302)

# -----------------------------
# 📊 STATS API
# -----------------------------
@app.get("/stats/{short_code}")
def get_stats(short_code: str):
    db: Session = SessionLocal()

    url = db.query(URL).filter(URL.short_code == short_code).first()

    if not url:
        raise HTTPException(status_code=404, detail="Not found")

    return {
        "long_url": url.long_url,
        "short_code": url.short_code,
        "click_count": url.click_count
    }


@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
    <head>
        <title>URL Shortener</title>

        <style>
            body {
                font-family: 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #667eea, #764ba2);
                height: 100vh;
                margin: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                transition: 0.3s;
            }

            .dark {
                background: #1a202c;
                color: white;
            }

            .container {
                background: white;
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                text-align: center;
                width: 420px;
                transition: 0.3s;
            }

            .dark .container {
                background: #2d3748;
            }

            input {
                width: 100%;
                padding: 10px;
                margin: 8px 0;
                border-radius: 8px;
                border: 1px solid #ccc;
            }

            button {
                width: 100%;
                padding: 10px;
                border: none;
                border-radius: 8px;
                background: #667eea;
                color: white;
                cursor: pointer;
                margin-top: 10px;
            }

            button:hover {
                background: #5a67d8;
            }

            .result {
                margin-top: 15px;
            }

            .error {
                color: red;
                margin-top: 10px;
            }

            .spinner {
                display: none;
                margin-top: 10px;
            }

            .toggle {
                position: absolute;
                top: 20px;
                right: 20px;
                cursor: pointer;
                background: white;
                padding: 8px;
                border-radius: 50%;
            }

            .dark .toggle {
                background: #2d3748;
                color: white;
            }
        </style>
    </head>

    <body>

        <div class="toggle" onclick="toggleDark()">🌙</div>

        <div class="container">
            <h2>🔗 URL Shortener</h2>

            <input id="urlInput" placeholder="Enter long URL">

            <input id="customCode" placeholder="Custom alias (optional)">

            <button onclick="shorten()">Shorten URL</button>

            <div class="spinner" id="spinner">⏳ Processing...</div>

            <div class="error" id="error"></div>

            <div class="result" id="result"></div>

            <button id="copyBtn" onclick="copyUrl()" style="display:none;">Copy 📋</button>

            <div id="stats"></div>
        </div>

        <script>
            let shortUrl = "";

            async function shorten() {
                document.getElementById("spinner").style.display = "block";
                document.getElementById("error").innerText = "";
                document.getElementById("result").innerHTML = "";
                document.getElementById("stats").innerHTML = "";

                const url = document.getElementById("urlInput").value;
                const custom = document.getElementById("customCode").value;

                try {
                    const response = await fetch("/shorten", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ url: url, custom_code: custom })
                    });

                    const data = await response.json();

                    if (data.detail) {
                        throw new Error(data.detail);
                    }

                    shortUrl = data.short_url;

                    document.getElementById("result").innerHTML =
                        `<a href="${shortUrl}" target="_blank">${shortUrl}</a>`;

                    document.getElementById("copyBtn").style.display = "block";

                    // Fetch stats
                    const code = shortUrl.split("/").pop();

// wait a bit before fetching stats
setTimeout(async () => {
    const statsRes = await fetch(`${window.location.origin}/stats/${code}`);
    const stats = await statsRes.json();

    document.getElementById("stats").innerHTML =
        `📊 Clicks: ${stats.click_count}`;
}, 800);

                } catch (err) {
                    document.getElementById("error").innerText = err.message;
                }

                document.getElementById("spinner").style.display = "none";
            }

            function copyUrl() {
                navigator.clipboard.writeText(shortUrl);
                alert("Copied!");
            }

            function toggleDark() {
                document.body.classList.toggle("dark");
            }
        </script>

    </body>
    </html>
    """

