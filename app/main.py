from fastapi import FastAPI
from app.routes import auth, predict
from app.db.session import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Safran AI API",
    version="1.0.0",
    description="JWT-based auth with manual login. Use /login to get a token, then paste 'Bearer <token>' into Authorize.",
)

app.include_router(auth.router)
app.include_router(predict.router)