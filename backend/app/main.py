from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models.schema_models import DatasetRequest, DatasetResponse
from app.services.dataset_generation_service import generate_normal_dataset
from app.services.export_service import (
    export_dataset_as_csv,
    export_dataset_as_json,
    export_dataset_as_pipe
)
from app.services.schema_inference_service import infer_schema_from_csv





app = FastAPI(
    title="Synthetic Test Data Generator",
    description="LLM-free internal platform for generating realistic, non-sensitive synthetic datasets for pipeline testing and regression.",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "status": "running",
        "service": "Synthetic Test Data Generator",
        "mode": "LLM-free",
        "data_policy": "synthetic-only"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@app.post("/validate-schema")
def validate_schema(request: DatasetRequest):
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
                "unique": column.unique
            }
            for column in request.columns
        ],
        "case_distribution": request.case_distribution.model_dump(),
        "synthetic_only": True
    }

@app.post("/generate", response_model=DatasetResponse)
def generate_dataset(request: DatasetRequest):
    return generate_normal_dataset(request)



@app.post("/export/json")
def export_json(request: DatasetRequest):
    dataset_result = generate_normal_dataset(request)
    return export_dataset_as_json(dataset_result)


@app.post("/export/csv")
def export_csv(request: DatasetRequest):
    dataset_result = generate_normal_dataset(request)
    return export_dataset_as_csv(dataset_result)

@app.post("/export/pipe")
def export_pipe(request: DatasetRequest):
    dataset_result = generate_normal_dataset(request)
    return export_dataset_as_pipe(dataset_result)

@app.post("/infer-schema")
def infer_schema(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported for schema inference."
        )

    try:
        return infer_schema_from_csv(file)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )