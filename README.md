# Image Classifier

This project is an image classification platform powered by **FastAPI** and **Streamlit**. Users can register, log in,
upload images, and get predictions using a pre-trained ONNX model. All predictions are securely stored and can be
accessed with detailed history and statistics.

---

## Live Demo

- **Deployed API (FastAPI)**: [https://safran-api.onrender.com/docs](https://safran-api.onrender.com/docs)
- **Streamlit UI**: [https://safran-ui.streamlit.app](https://safran-ui.streamlit.app)

## Tech Stack

- **Backend**: FastAPI + ONNX + SQLAlchemy + SQLite/PostgreSQL
- **Frontend**: Streamlit
- **Authentication**: JWT (OAuth2 Password Bearer)
- **Model**: ResNet18 in ONNX format

---

## Backend API (FastAPI)

### Requirements

Install dependencies:

```bash
pip install -r requirements.txt
```

### Run the FastAPI server

```bash
uvicorn app.main:app --reload
```

### API Documentation

Once running locally:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

Deployed version:

- **Deployed API (FastAPI)**: [https://safran-api.onrender.com/docs](https://safran-api.onrender.com/docs)
- **Streamlit UI**: [https://safran-ui.streamlit.app](https://safran-ui.streamlit.app)

---

### Auth Endpoints

| Method | Route     | Description                       |
|--------|-----------|-----------------------------------|
| POST   | /register | Register a new user               |
| POST   | /login    | Authenticate and return JWT token |

---

### Prediction Endpoints

| Method | Route                   | Description                            |
|--------|-------------------------|----------------------------------------|
| POST   | /predict                | Predict a single image                 |
| POST   | /predict-multiple       | Predict multiple images                |
| GET    | /predictions            | List authenticated user’s predictions  |
| GET    | /predictions/{id}       | Get details for one prediction         |
| GET    | /predictions/{id}/image | Get uploaded image for that prediction |
| GET    | /stats                  | Get stats grouped by predicted label   |

---

## Frontend UI (Streamlit)

### Run the Streamlit app

```bash
streamlit run streamlit_app.py
```

> ✅ Make sure the FastAPI backend is running **before** launching Streamlit.

### Features

- User registration and login
- JWT-based token storage with session
- Upload and classify `.jpg`, `.png`, `.webp` images
- View prediction history and see uploaded images
- View statistics of predictions
- Log out to reset session

---

## Environment Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows
pip install -r requirements.txt
```

---

## Folder Structure

```
.
├── app/
│   ├── main.py
│   ├── models/
│   ├── routes/
│   ├── schemas/
│   ├── services/
│   └── db/
├── streamlit_app.py
├── requirements.txt
└── README.md
```

---

## Example Usage (Swagger)

1. Go to `http://localhost:8000/docs`
2. Register a new user via `/register`
3. Log in using `/login` and copy the access token
4. Click the 🔒 "Authorize" button and paste the token as `Bearer <token>`
5. Now you can call `/predict`, `/predictions`, `/stats`, etc.

---

## Model Info

- ONNX model used: `resnet18.onnx`
- Supports: `.jpg`, `.jpeg`, `.png`, `.webp`
- Automatically saves predictions and user inputs to database

---
