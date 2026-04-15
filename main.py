# from fastapi import FastAPI, HTTPException
# from fastapi.responses import RedirectResponse
# from sqlalchemy.orm import Session
# from database import SessionLocal, engine, Base
# from models import URL
# from base62 import encode
# import validators
# import redis

# r = redis.Redis(host='localhost', port=6379, db=0)

# Base.metadata.create_all(bind=engine)

# app = FastAPI()

# def get_db():
#     db = SessionLocal()
#     try:
#         return db
#     finally:
#         db.close()

# @app.post("/shorten")
# def shorten_url(request: dict):
#     db: Session = SessionLocal()

#     long_url = request.get("url")
#     custom_code = request.get("custom_code")

#     if not validators.url(long_url):
#         raise HTTPException(status_code=400, detail="Invalid URL")

#     # ✅ If custom alias is provided
#     if custom_code:
#         existing = db.query(URL).filter(URL.short_code == custom_code).first()
#         if existing:
#             raise HTTPException(status_code=400, detail="Custom code already exists")

#         short_code = custom_code

#         new_url = URL(long_url=long_url, short_code=short_code)
#         db.add(new_url)
#         db.commit()

#         return {"short_url": f"http://localhost:8000/{short_code}"}

#     # ✅ Default Base62 logic
#     new_url = URL(long_url=long_url)
#     db.add(new_url)
#     db.commit()
#     db.refresh(new_url)

#     short_code = encode(new_url.id)
#     new_url.short_code = short_code
#     db.commit()

#     return {"short_url": f"http://localhost:8000/{short_code}"}

# @app.get("/stats/{short_code}")
# def get_stats(short_code: str):
#     db: Session = SessionLocal()

#     url = db.query(URL).filter(URL.short_code == short_code).first()

#     if not url:

#         raise HTTPException(status_code=404, detail="Not found")

#     return {
#         "long_url": url.long_url,
#         "click_count": url.click_count
#     }

from fastapi import FastAPI, HTTPException 
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import URL
from base62 import encode
import validators
import redis

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

    return {"short_url": f"http://localhost:8000/{short_code}"}


# -----------------------------
# 🔁 REDIRECT API
# -----------------------------

@app.get("/{short_code}")
def redirect(short_code: str):
    db: Session = SessionLocal()

    # ✅ Try cache
    try:
        cached_url = r.get(short_code)
    except:
        cached_url = None

    if cached_url:
        # 🔥 IMPORTANT: update click count even if cache hit
        url = db.query(URL).filter(URL.short_code == short_code).first()
        if url:
            url.click_count += 1
            db.commit()

        return RedirectResponse(url=cached_url.decode(), status_code=302)

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