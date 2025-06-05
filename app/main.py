from fastapi import FastAPI

from app.db.session import engine, Base
from app.routes import auth, predict

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Safran AI Prediction API",
    version="1.0.0",
    description="""
Safran AI API enables users to perform image-based predictions using a deep learning model (ONNX runtime). The API offers authentication, inference, and data retrieval features.

---

### 🔐 Authentication & Access

To use the protected endpoints, follow these steps:

1. **Register:**  
   - Go to **`/register`** and POST a JSON body with your email and password:
     ```json
     {
       "email": "your_email@example.com",
       "password": "your_secure_password"
     }
     ```

2. **Login to get a JWT token:**  
   - Go to **`/login`** and submit the same credentials.
   - You will receive a response with an `access_token`.

3. **Authorize in Swagger:**  
   - Click the **Authorize 🔒** button (top right).
   - Paste the token like this:  
     ```
     Bearer <your_token>
     ```

---

### 📌 API Features

- 🔸 `POST /register`: Create a new user account  
- 🔸 `POST /login`: Get your JWT token  
- 🔸 `POST /predict`: Submit a single image for prediction  
- 🔸 `POST /predict-multiple`: Submit multiple images at once  
- 🔸 `GET /predictions`: View your prediction history  
- 🔸 `GET /predictions/{id}`: See details of a specific prediction  
- 🔸 `GET /predictions/{id}/image`: View/download the original uploaded image  
- 🔸 `GET /stats`: Get class-based prediction statistics

---

Use this API to power secure, user-specific AI inference workflows.
""",
    swagger_ui_init_oauth={"usePkceWithAuthorizationCodeGrant": False}
)

app.include_router(auth.router)
app.include_router(predict.router)