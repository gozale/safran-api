from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.schemas.prediction import PredictionInput, PredictionOutput, PredictionRecord
from app.db.session import SessionLocal
from app.models.prediction import Prediction
from app.models.user import User
from app.services.inference import run_model
from jose import JWTError, jwt
from app.auth.token_scheme import oauth2_scheme
from fastapi.security import HTTPAuthorizationCredentials
from typing import List
from fastapi.responses import StreamingResponse, JSONResponse
import io

router = APIRouter()

SECRET_KEY = "yoursecretkey"
ALGORITHM = "HS256"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: HTTPAuthorizationCredentials = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        user = db.query(User).filter(User.email == email).first()
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/predict", response_model=PredictionOutput)
def predict(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    image_bytes = file.file.read()
    result = run_model(image_bytes)
    pred = Prediction(
        user_id=user.id,
        input_data={"filename": file.filename},
        output_data={"result": result},
        image_data=image_bytes
    )
    db.add(pred)
    db.commit()
    return {"result": result}

from app.schemas.prediction import PredictionRecord

@router.get("/predictions", response_model=List[PredictionRecord])
def get_user_predictions(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Do NOT include image_base64 in list
    return [PredictionRecord.from_orm_with_image(p, include_image=False) for p in db.query(Prediction).filter(Prediction.user_id == user.id).all()]

@router.get("/predictions/{id}", response_model=PredictionRecord)
def get_prediction_by_id(
    id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    prediction = db.query(Prediction).filter(Prediction.id == id, Prediction.user_id == user.id).first()
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return PredictionRecord.from_orm_with_image(prediction, include_image=True)

@router.get("/predictions/{id}/image")
def get_prediction_image(
    id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    prediction = db.query(Prediction).filter(Prediction.id == id, Prediction.user_id == user.id).first()
    if not prediction or not prediction.image_data:
        raise HTTPException(status_code=404, detail="Image not found")

    return StreamingResponse(
        io.BytesIO(prediction.image_data),
        media_type="image/jpeg",
        headers={"Content-Disposition": f"inline; filename=prediction_{id}.jpg"}
    )

@router.post("/predict-multiple")
def predict_multiple(
    files: List[UploadFile] = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    results = []

    for file in files:
        image_bytes = file.file.read()
        result = run_model(image_bytes)

        # Save each prediction to the database
        pred = Prediction(
            user_id=user.id,
            input_data={"filename": file.filename},
            output_data={"result": result},
            image_data=image_bytes
        )
        db.add(pred)
        db.commit()
        db.refresh(pred)

        results.append({
            "filename": file.filename,
            "result": result,
            "prediction_id": pred.id,
            "image_url": f"/predictions/{pred.id}/image"
        })

    return JSONResponse(content={"predictions": results})

@router.get("/stats", summary="Get prediction statistics", description="Returns the number of predictions grouped by class label.")
def get_prediction_stats(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    results = (
        db.query(Prediction.output_data["result"].as_string(), func.count(Prediction.id))
        .filter(Prediction.user_id == user.id)
        .group_by(Prediction.output_data["result"].as_string())
        .all()
    )

    return JSONResponse(content={"stats": dict(results)})