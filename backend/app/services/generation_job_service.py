from datetime import UTC, datetime, timedelta
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.db.models import Dataset, GenerationOutput, GenerationRun, GenerationStatus, OutputFormat, QualityReport, SchemaVersion, SchemaVersionTrigger
from app.repositories.schema_version import SchemaVersionRepository
from app.services.artifact_packaging_service import connected_zip_bytes, json_bytes
from app.services.connected_generation_service import generate_connected_dataset
from app.services.dataset_generation_service import generate_normal_dataset
from app.services.rules_engine import apply_rules
from app.models.schema_models import DatasetRequest
from app.storage import LocalArtifactStorage

class GenerationJobService:
    def __init__(self,session:AsyncSession,storage=None): self.session=session;self.storage=storage or LocalArtifactStorage()

    async def submit(self,*,dataset:Dataset,user_id:UUID,row_total:int,seed:int|None,output_format:OutputFormat,idempotency_key:str)->GenerationRun:
        existing=(await self.session.execute(select(GenerationRun).where(GenerationRun.requested_by==user_id,GenerationRun.idempotency_key==idempotency_key))).scalar_one_or_none()
        if existing:return existing
        version=await SchemaVersionRepository(self.session).create_next(dataset_id=dataset.id,created_by=user_id,trigger=SchemaVersionTrigger.GENERATION,schema_document=dataset.draft_schema_document)
        run=GenerationRun(dataset_id=dataset.id,schema_version_id=version.id,requested_by=user_id,seed=seed,status=GenerationStatus.QUEUED,progress_percent=0,requested_row_total=row_total,generated_row_total=0,idempotency_key=idempotency_key,current_phase="queued",cancel_requested=False)
        self.session.add(run);await self.session.commit();await self.session.refresh(run);return run

    async def execute(self,run_id:UUID)->None:
        run=await self.session.get(GenerationRun,run_id)
        if not run or run.status != GenerationStatus.QUEUED:return
        try:
            run.status=GenerationStatus.RUNNING;run.current_phase="validating";run.progress_percent=10;run.started_at=datetime.now(UTC);await self.session.commit()
            version=await self.session.get(SchemaVersion,run.schema_version_id);schema=version.schema_document
            if run.cancel_requested: await self._cancel(run);return
            run.current_phase="generating";run.progress_percent=35;await self.session.commit()
            if schema.get("tables"):
                tables,relationship_report=generate_connected_dataset(schema,run.seed)
                for name,rows in tables.items():
                    rules=next((t.get("rules",[]) for t in schema["tables"] if t["name"]==name),[])
                    applied=apply_rules(rows,rules);tables[name]=applied.rows
                quality={"relationship_report":relationship_report,"status":"pass" if relationship_report["valid"] else "fail"}
                content=connected_zip_bytes(tables,schema,relationship_report,quality);fmt=OutputFormat.ZIP;generated=sum(map(len,tables.values()))
            else:
                request=DatasetRequest.model_validate({**schema,"row_count":run.requested_row_total,"seed":run.seed})
                result=generate_normal_dataset(request)
                applied=apply_rules(result.generated_rows,schema.get("rules",[]))
                content=json_bytes({"rows":applied.rows,"violations":applied.violations,"summary":result.summary.model_dump()});fmt=OutputFormat.JSON;generated=len(applied.rows);quality={"violations":applied.violations,"status":"pass" if not applied.violations else "warning"}
            if run.cancel_requested: await self._cancel(run);return
            run.current_phase="packaging";run.progress_percent=80;await self.session.commit()
            object_path=f"{run.requested_by}/{run.id}/output.{fmt.value}"
            artifact=self.storage.write(object_path,content)
            expires=datetime.now(UTC)+timedelta(hours=get_settings().generated_file_retention_hours)
            self.session.add(GenerationOutput(generation_id=run.id,object_path=artifact.object_path,output_format=fmt,size_bytes=artifact.size_bytes,checksum_sha256=artifact.checksum_sha256,expires_at=expires))
            self.session.add(QualityReport(generation_id=run.id,report_document=quality,score=100.0 if quality["status"]=="pass" else None,status=quality["status"]))
            run.status=GenerationStatus.COMPLETED;run.current_phase="completed";run.progress_percent=100;run.generated_row_total=generated;run.completed_at=datetime.now(UTC);await self.session.commit()
        except Exception as error:
            await self.session.rollback();run=await self.session.get(GenerationRun,run_id)
            if run:run.status=GenerationStatus.FAILED;run.current_phase="failed";run.failure_code="generation_failed";run.failure_message=str(error)[:1000];run.completed_at=datetime.now(UTC);await self.session.commit()

    async def _cancel(self,run):
        run.status=GenerationStatus.CANCELLED;run.current_phase="cancelled";run.completed_at=datetime.now(UTC);await self.session.commit()
