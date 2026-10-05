from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_current_user
from app.db.models import Dataset, GenerationOutput, GenerationRun, GenerationStatus, OutputFormat, User
from app.db.session import AsyncSessionFactory, get_database_session
from app.repositories.dataset_storage import DatasetAccessRepository
from app.schemas.generation_platform import GenerationOutputResponse, GenerationResponse, GenerationSubmit
from app.services.generation_job_service import GenerationJobService
from app.storage import LocalArtifactStorage

router=APIRouter(prefix="/generation-jobs",tags=["generation jobs"])

async def execute_background(run_id):
    async with AsyncSessionFactory() as session: await GenerationJobService(session).execute(run_id)

async def owned_run(run_id,user,session):
    run=await session.get(GenerationRun,run_id)
    if not run or run.requested_by != user.id: raise HTTPException(404,"Generation job not found.")
    return run

@router.post("",response_model=GenerationResponse,status_code=202)
async def submit(payload:GenerationSubmit,tasks:BackgroundTasks,user:Annotated[User,Depends(get_current_user)],session:Annotated[AsyncSession,Depends(get_database_session)]):
    dataset,permission=await DatasetAccessRepository(session).get_accessible(payload.dataset_id,user.id)
    if not dataset: raise HTTPException(404,"Dataset not found.")
    run=await GenerationJobService(session).submit(dataset=dataset,user_id=user.id,row_total=payload.requested_row_total,seed=payload.seed,output_format=payload.output_format,idempotency_key=payload.idempotency_key)
    tasks.add_task(execute_background,run.id);return run

@router.get("",response_model=list[GenerationResponse])
async def history(user:Annotated[User,Depends(get_current_user)],session:Annotated[AsyncSession,Depends(get_database_session)]):
    return (await session.execute(select(GenerationRun).where(GenerationRun.requested_by==user.id).order_by(GenerationRun.created_at.desc()).limit(100))).scalars().all()

@router.get("/{run_id}",response_model=GenerationResponse)
async def detail(run_id:UUID,user:Annotated[User,Depends(get_current_user)],session:Annotated[AsyncSession,Depends(get_database_session)]): return await owned_run(run_id,user,session)

@router.post("/{run_id}/cancel",response_model=GenerationResponse)
async def cancel(run_id:UUID,user:Annotated[User,Depends(get_current_user)],session:Annotated[AsyncSession,Depends(get_database_session)]):
    run=await owned_run(run_id,user,session)
    if run.status not in {GenerationStatus.QUEUED,GenerationStatus.RUNNING}: raise HTTPException(409,"Generation job cannot be cancelled.")
    run.cancel_requested=True;await session.commit();await session.refresh(run);return run

@router.post("/{run_id}/retry",response_model=GenerationResponse,status_code=202)
async def retry(run_id:UUID,tasks:BackgroundTasks,user:Annotated[User,Depends(get_current_user)],session:Annotated[AsyncSession,Depends(get_database_session)]):
    source=await owned_run(run_id,user,session);dataset=await session.get(Dataset,source.dataset_id)
    output=(await session.execute(select(GenerationOutput).where(GenerationOutput.generation_id==source.id).limit(1))).scalar_one_or_none()
    run=await GenerationJobService(session).submit(dataset=dataset,user_id=user.id,row_total=source.requested_row_total,seed=source.seed,output_format=output.output_format if output else OutputFormat.JSON,idempotency_key=f"retry-{source.id}-{datetime.now(UTC).timestamp()}")
    tasks.add_task(execute_background,run.id);return run

@router.get("/{run_id}/outputs",response_model=list[GenerationOutputResponse])
async def outputs(run_id:UUID,user:Annotated[User,Depends(get_current_user)],session:Annotated[AsyncSession,Depends(get_database_session)]):
    await owned_run(run_id,user,session);return (await session.execute(select(GenerationOutput).where(GenerationOutput.generation_id==run_id))).scalars().all()

@router.get("/{run_id}/outputs/{output_id}/download")
async def download(run_id:UUID,output_id:UUID,user:Annotated[User,Depends(get_current_user)],session:Annotated[AsyncSession,Depends(get_database_session)]):
    await owned_run(run_id,user,session);output=await session.get(GenerationOutput,output_id)
    if not output or output.generation_id!=run_id or output.deleted_at or output.expires_at<=datetime.now(UTC):raise HTTPException(404,"Output is unavailable.")
    try:path=LocalArtifactStorage().path(output.object_path)
    except FileNotFoundError as error:raise HTTPException(404,"Output is unavailable.") from error
    return FileResponse(path,filename=path.name)

@router.delete("/{run_id}/outputs/{output_id}",status_code=204)
async def delete_output(run_id:UUID,output_id:UUID,user:Annotated[User,Depends(get_current_user)],session:Annotated[AsyncSession,Depends(get_database_session)]):
    await owned_run(run_id,user,session);output=await session.get(GenerationOutput,output_id)
    if not output or output.generation_id!=run_id:raise HTTPException(404,"Output not found.")
    LocalArtifactStorage().delete(output.object_path);output.deleted_at=datetime.now(UTC);await session.commit();return Response(status_code=204)
