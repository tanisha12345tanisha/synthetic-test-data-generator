from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_current_user
from app.db.models import Dataset, DatasetShare, DatasetStatus, SchemaVersion, SchemaVersionTrigger, SharePermission, User
from app.db.session import get_database_session
from app.repositories.dataset_storage import DatasetAccessRepository
from app.repositories.schema_version import SchemaVersionRepository
from app.repositories.user import UserRepository
from app.schemas.dataset_storage import DatasetCreate, DatasetListResponse, DatasetResponse, DatasetUpdate, SchemaVersionResponse, ShareCreate, ShareResponse, VersionCreate

router = APIRouter(prefix="/datasets", tags=["datasets"])

def response(dataset: Dataset, permission=None):
    item = DatasetResponse.model_validate(dataset)
    return item.model_copy(update={"permission": permission})

def can_edit(dataset: Dataset, user: User, permission):
    return dataset.owner_id == user.id or permission == SharePermission.EDITOR

async def accessible(dataset_id, user, session):
    dataset, permission = await DatasetAccessRepository(session).get_accessible(dataset_id, user.id)
    if not dataset: raise HTTPException(404, "Dataset not found.")
    return dataset, permission

@router.post("", response_model=DatasetResponse, status_code=201)
async def create_dataset(payload: DatasetCreate, user: Annotated[User, Depends(get_current_user)], session: Annotated[AsyncSession, Depends(get_database_session)]):
    dataset = Dataset(owner_id=user.id, name=payload.name.strip(), description=payload.description, dataset_type=payload.dataset_type, input_mode=payload.input_mode, draft_schema_document=payload.schema_document)
    session.add(dataset); await session.flush()
    if payload.schema_document:
        await SchemaVersionRepository(session).create_next(dataset_id=dataset.id, created_by=user.id, trigger=SchemaVersionTrigger.MANUAL_SAVE, schema_document=payload.schema_document)
        dataset.current_draft_revision = 1
    await session.commit(); await session.refresh(dataset)
    return response(dataset)

@router.get("", response_model=DatasetListResponse)
async def list_datasets(user: Annotated[User, Depends(get_current_user)], session: Annotated[AsyncSession, Depends(get_database_session)], offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100)):
    rows = await DatasetAccessRepository(session).list_accessible(user.id, offset, limit)
    return DatasetListResponse(items=[response(d,p) for d,p in rows], offset=offset, limit=limit)

@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(dataset_id: UUID, user: Annotated[User, Depends(get_current_user)], session: Annotated[AsyncSession, Depends(get_database_session)]):
    dataset, permission = await accessible(dataset_id,user,session); return response(dataset,permission)

@router.patch("/{dataset_id}", response_model=DatasetResponse)
async def update_dataset(dataset_id: UUID, payload: DatasetUpdate, user: Annotated[User, Depends(get_current_user)], session: Annotated[AsyncSession, Depends(get_database_session)]):
    dataset, permission = await accessible(dataset_id,user,session)
    if not can_edit(dataset,user,permission): raise HTTPException(403,"Editor access required.")
    values=payload.model_dump(exclude_unset=True)
    schema=values.pop("schema_document",None)
    for key,value in values.items(): setattr(dataset,key,value)
    if schema is not None:
        dataset.draft_schema_document=schema; dataset.current_draft_revision += 1
    await session.commit(); await session.refresh(dataset); return response(dataset,permission)

@router.delete("/{dataset_id}", status_code=204)
async def delete_dataset(dataset_id: UUID, user: Annotated[User, Depends(get_current_user)], session: Annotated[AsyncSession, Depends(get_database_session)]):
    dataset, _ = await accessible(dataset_id,user,session)
    if dataset.owner_id != user.id: raise HTTPException(403,"Owner access required.")
    await session.delete(dataset); await session.commit(); return Response(status_code=204)

@router.post("/{dataset_id}/versions", response_model=SchemaVersionResponse, status_code=201)
async def create_version(dataset_id: UUID, payload: VersionCreate, user: Annotated[User, Depends(get_current_user)], session: Annotated[AsyncSession, Depends(get_database_session)]):
    dataset, permission = await accessible(dataset_id,user,session)
    if not can_edit(dataset,user,permission): raise HTTPException(403,"Editor access required.")
    version=await SchemaVersionRepository(session).create_next(dataset_id=dataset.id,created_by=user.id,trigger=payload.trigger,schema_document=dataset.draft_schema_document)
    await session.commit(); await session.refresh(version); return version

@router.get("/{dataset_id}/versions", response_model=list[SchemaVersionResponse])
async def list_versions(dataset_id: UUID, user: Annotated[User, Depends(get_current_user)], session: Annotated[AsyncSession, Depends(get_database_session)]):
    await accessible(dataset_id,user,session); return await SchemaVersionRepository(session).list_for_dataset(dataset_id)

@router.post("/{dataset_id}/versions/{version_id}/restore", response_model=DatasetResponse)
async def restore_version(dataset_id: UUID, version_id: UUID, user: Annotated[User, Depends(get_current_user)], session: Annotated[AsyncSession, Depends(get_database_session)]):
    dataset, permission=await accessible(dataset_id,user,session)
    if not can_edit(dataset,user,permission): raise HTTPException(403,"Editor access required.")
    version=await session.get(SchemaVersion,version_id)
    if not version or version.dataset_id != dataset.id: raise HTTPException(404,"Schema version not found.")
    dataset.draft_schema_document=version.schema_document; dataset.current_draft_revision += 1
    await SchemaVersionRepository(session).create_next(dataset_id=dataset.id,created_by=user.id,trigger=SchemaVersionTrigger.RESTORE,schema_document=version.schema_document,restored_from_version_id=version.id)
    await session.commit(); await session.refresh(dataset); return response(dataset,permission)

@router.get("/{dataset_id}/schema-export")
async def export_schema(dataset_id: UUID, user: Annotated[User, Depends(get_current_user)], session: Annotated[AsyncSession, Depends(get_database_session)]):
    dataset,_=await accessible(dataset_id,user,session); return {"dataset_name":dataset.name,"schema_document":dataset.draft_schema_document}

@router.post("/{dataset_id}/shares", response_model=ShareResponse, status_code=201)
async def share_dataset(dataset_id: UUID, payload: ShareCreate, user: Annotated[User, Depends(get_current_user)], session: Annotated[AsyncSession, Depends(get_database_session)]):
    dataset,_=await accessible(dataset_id,user,session)
    if dataset.owner_id != user.id: raise HTTPException(403,"Owner access required.")
    target=await UserRepository(session).get_by_email(str(payload.email))
    if not target or target.id == user.id: raise HTTPException(400,"A valid different user account is required.")
    existing=(await session.execute(select(DatasetShare).where(DatasetShare.dataset_id==dataset.id,DatasetShare.user_id==target.id))).scalar_one_or_none()
    if existing: existing.permission=payload.permission; share=existing
    else:
        share=DatasetShare(dataset_id=dataset.id,user_id=target.id,granted_by=user.id,permission=payload.permission);session.add(share)
    await session.commit();await session.refresh(share)
    return ShareResponse(id=share.id,user_id=target.id,email=target.email,display_name=target.display_name,permission=share.permission,created_at=share.created_at)

@router.get("/{dataset_id}/shares", response_model=list[ShareResponse])
async def list_shares(dataset_id: UUID, user: Annotated[User, Depends(get_current_user)], session: Annotated[AsyncSession, Depends(get_database_session)]):
    dataset,_=await accessible(dataset_id,user,session)
    if dataset.owner_id != user.id: raise HTTPException(403,"Owner access required.")
    rows=(await session.execute(select(DatasetShare,User).join(User,User.id==DatasetShare.user_id).where(DatasetShare.dataset_id==dataset.id))).all()
    return [ShareResponse(id=s.id,user_id=u.id,email=u.email,display_name=u.display_name,permission=s.permission,created_at=s.created_at) for s,u in rows]

@router.delete("/{dataset_id}/shares/{target_user_id}", status_code=204)
async def revoke_share(dataset_id: UUID,target_user_id:UUID,user:Annotated[User,Depends(get_current_user)],session:Annotated[AsyncSession,Depends(get_database_session)]):
    dataset,_=await accessible(dataset_id,user,session)
    if dataset.owner_id != user.id: raise HTTPException(403,"Owner access required.")
    await session.execute(delete(DatasetShare).where(DatasetShare.dataset_id==dataset.id,DatasetShare.user_id==target_user_id));await session.commit();return Response(status_code=204)
