from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.datasets import router as datasets_router
from app.api.dependencies import get_current_user
from app.db.models import User
from app.models.schema_models import DatasetRequest
from app.services.dataset_generation_service import generate_normal_dataset
from app.services.export_service import (
    export_dataset_as_csv,
    export_dataset_as_json,
    export_dataset_as_pipe,
)
from app.services.schema_inference_service import infer_schema_from_csv


app = FastAPI(
    title="Synthetic Test Data Generator",
    description=(
        "Internal platform for generating realistic, non-sensitive "
        "synthetic datasets for pipeline testing and regression."
    ),
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(datasets_router)

@app.get("/")
def root():
    return {
        "status": "running",
        "service": "Synthetic Test Data Generator",
        "mode": "LLM-free",
        "data_policy": "synthetic-only",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


@app.post("/validate-schema")
def validate_schema(request: DatasetRequest, _user: User = Depends(get_current_user)):
    return {
        "valid": True,
        "message": "Schema is valid.",
        "dataset_name": request.dataset_name,
        "row_count": request.row_count,
        "seed": request.seed,
        "total_columns": len(request.columns),
        "columns": [
            {
                "name": column.name,
                "type": column.type,
                "required": column.required,
                "nullable": column.nullable,
                "unique": column.unique,
            }
            for column in request.columns
        ],
        "case_distribution": request.case_distribution.model_dump(),
        "synthetic_only": True,
    }


@app.post("/generate")
def generate_dataset(request: DatasetRequest, _user: User = Depends(get_current_user)):
    return generate_normal_dataset(request)


@app.post("/export/json")
def export_json(request: DatasetRequest, _user: User = Depends(get_current_user)):
    dataset_result = generate_normal_dataset(request)
    return export_dataset_as_json(dataset_result)


@app.post("/export/csv")
def export_csv(request: DatasetRequest, _user: User = Depends(get_current_user)):
    dataset_result = generate_normal_dataset(request)
    return export_dataset_as_csv(dataset_result)


@app.post("/export/pipe")
def export_pipe(request: DatasetRequest, _user: User = Depends(get_current_user)):
    dataset_result = generate_normal_dataset(request)
    return export_dataset_as_pipe(dataset_result)


@app.post("/infer-schema")
def infer_schema(file: UploadFile = File(...), _user: User = Depends(get_current_user)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported for schema inference.",
        )

    try:
        return infer_schema_from_csv(file)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error