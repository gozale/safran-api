import io
from typing import List

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.security import HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.token_scheme import oauth2_scheme
from app.db.session import SessionLocal
from app.models.prediction import Prediction
from app.models.user import User
from app.schemas.prediction import PredictionOutput, PredictionRecord
from app.services.inference import run_model

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


@router.post(
    "/predict",
    response_model=PredictionOutput,
    summary="Run prediction on one image",
    description="Accepts a JPEG/PNG/WEBP image, performs inference using ResNet18, and stores the prediction in the database.",
    responses={
        200: {"description": "Prediction successful"},
        400: {"description": "Unsupported file type"},
        401: {"description": "Unauthorized"},
        500: {"description": "Internal server error"},
    },
)
def predict(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
        raise HTTPException(status_code=400,
                            detail="Unsupported file type. Please upload a .jpg, .png, or .webp image.")

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


@router.post(
    "/predict-multiple",
    summary="Run prediction on multiple images",
    description="Accepts multiple JPEG/PNG/WEBP images and returns a list of predictions with image URLs. Stores all predictions in DB.",
    responses={
        200: {"description": "Batch prediction successful"},
        400: {"description": "One or more files are not supported image types"},
        401: {"description": "Unauthorized"},
    },
)
def predict_multiple(
    files: List[UploadFile] = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    results = []

    for file in files:
        if not file.filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.filename}")

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
        db.refresh(pred)

        results.append({
            "filename": file.filename,
            "result": result,
            "prediction_id": pred.id,
            "image_url": f"/predictions/{pred.id}/image"
        })

    return JSONResponse(content={"predictions": results})


@router.get(
    "/predictions",
    response_model=List[PredictionRecord],
    summary="Get prediction history",
    description="Returns all predictions made by the authenticated user. Image is not included in this view."
)
def get_user_predictions(
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    predictions = db.query(Prediction).filter(Prediction.user_id == user.id).all()
    return [PredictionRecord.from_orm_with_image(p, include_image=False) for p in predictions]


@router.get(
    "/predictions/{id}",
    response_model=PredictionRecord,
    summary="Get a specific prediction",
    description="Retrieve detailed prediction info (without the image) by ID if the prediction belongs to the authenticated user."
)
def get_prediction_by_id(
        id: int,
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    prediction = db.query(Prediction).filter(Prediction.id == id, Prediction.user_id == user.id).first()
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return PredictionRecord.from_orm_with_image(prediction, include_image=False)


@router.get(
    "/predictions/{id}/image",
    summary="Get the uploaded image",
    description="Streams the original uploaded image of the prediction as JPEG."
)
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


@router.get(
    "/stats",
    summary="Get prediction statistics",
    description="Returns the number of predictions grouped by class label.",
    responses={
        200: {"description": "Statistics returned successfully"},
        401: {"description": "Unauthorized"}
    },
)
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