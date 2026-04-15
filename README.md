# 🔗 URL Shortener

A scalable URL Shortener built using FastAPI that converts long URLs into short, shareable links. It uses Base62 encoding with auto-increment IDs to ensure uniqueness and efficiency.

---

## 🚀 Features

* 🔗 Shorten long URLs
* ✏️ Custom aliases (e.g., /punith)
* 📊 Click tracking (analytics)
* 🔐 URL validation
* ⚡ Redis caching (with fallback support)
* 🌍 Ready for deployment (Render / ngrok)

---

## 🧠 Core Logic

* Uses **auto-increment ID + Base62 encoding**
* Ensures **unique short URLs without collisions**
* Example:
  ID → 125 → Base62 → `cb`

---

## 🛠️ Tech Stack

* Backend: FastAPI
* Database: SQLite (can upgrade to PostgreSQL)
* ORM: SQLAlchemy
* Cache: Redis (optional)
* Server: Uvicorn

---

## 📂 Project Structure

```
url_shortener/
│
├── main.py          # API routes
├── models.py        # Database model
├── database.py      # DB connection
├── base62.py        # Encoding logic
├── requirements.txt
```

---

## ▶️ How to Run Locally

```bash
# Clone repo
git clone https://github.com/your-username/url-shortener.git

cd url-shortener

# Create virtual environment
python -m venv venv
venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn main:app --reload
```

---

## 🌐 API Endpoints

### 🔹 Shorten URL

POST `/shorten`

```json
{
  "url": "https://example.com",
  "custom_code": "optional"
}
```

---

### 🔹 Redirect

GET `/{short_code}`

---

### 🔹 Analytics

GET `/stats/{short_code}`

---

## ⚡ Deployment

The project can be deployed on:

* Render
* Railway
* AWS

Set environment variable:

```
BASE_URL=https://your-domain.com
```

---

## 🎯 Future Improvements

* Link expiration (TTL)
* User authentication
* Advanced analytics dashboard
* Custom domain support

---

## 🧠 Key Learnings

* System design of URL shorteners
* Base62 encoding
* Caching strategies and trade-offs
* Backend API development
* Deployment practices

---

## 👨‍💻 Author

Punith Kumar

---
