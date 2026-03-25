import pathlib
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from typing import List
import structlog

from .. import models, schemas
from ..auth import get_current_user
from ..database import get_db

router = APIRouter(tags=["performances"])
log = structlog.get_logger(__name__)

BACKEND_DIR = pathlib.Path(__file__).resolve().parent.parent
UPLOADS_DIR = BACKEND_DIR / "uploads"

_FILE_HEAD_LINES = 5


def _head_lines(text: str, n: int = _FILE_HEAD_LINES) -> str:
    """Return the first *n* lines of *text* for debug logging."""
    lines = text.splitlines()
    head = "\n".join(lines[:n])
    if len(lines) > n:
        head += f"\n… ({len(lines) - n} more lines)"
    return head


def get_touch_or_404(touch_id: int, user: models.User, db: Session) -> models.Touch:
    touch = db.query(models.Touch).filter(
        models.Touch.id == touch_id, models.Touch.user_id == user.id
    ).first()
    if not touch:
        raise HTTPException(status_code=404, detail="Touch not found")
    return touch


def get_performance_or_404(performance_id: int, touch_id: int, db: Session) -> models.Performance:
    perf = db.query(models.Performance).filter(
        models.Performance.id == performance_id,
        models.Performance.touch_id == touch_id,
    ).first()
    if not perf:
        raise HTTPException(status_code=404, detail="Performance not found")
    return perf


@router.get("/api/touches/{touch_id}/performances", response_model=list[schemas.PerformanceRead])
def list_performances(touch_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    get_touch_or_404(touch_id, current_user, db)
    perfs = db.query(models.Performance).filter(models.Performance.touch_id == touch_id).order_by(models.Performance.order_index).all()
    log.debug(
        "performances_listed",
        touch_id=touch_id,
        count=len(perfs),
        user_id=current_user.id,
        performance_ids=[p.id for p in perfs],
        labels=[p.label for p in perfs],
    )
    return perfs


@router.post("/api/touches/{touch_id}/performances", response_model=schemas.PerformanceRead, status_code=status.HTTP_201_CREATED)
async def create_performance(
    touch_id: int,
    label: str = Form(...),
    order_index: int = Form(0),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    get_touch_or_404(touch_id, current_user, db)
    log.debug(
        "performance_upload_started",
        touch_id=touch_id,
        label=label,
        order_index=order_index,
        filename=file.filename,
        content_type=file.content_type,
        user_id=current_user.id,
    )
    perf = models.Performance(touch_id=touch_id, label=label, order_index=order_index)
    db.add(perf)
    db.commit()
    db.refresh(perf)
    content = await file.read()
    text = content.decode("utf-8", errors="replace")
    log.debug(
        "timing_file_head",
        touch_id=touch_id,
        performance_id=perf.id,
        filename=file.filename,
        total_lines=len(text.splitlines()),
        head=_head_lines(text),
    )
    timings_dir = UPLOADS_DIR / "timings" / str(touch_id)
    timings_dir.mkdir(parents=True, exist_ok=True)
    file_path = timings_dir / f"{perf.id}.csv"
    file_path.write_bytes(content)
    perf.timing_file_path = str(file_path)
    db.commit()
    db.refresh(perf)
    log.info("performance_created", performance_id=perf.id, touch_id=touch_id, label=label, user_id=current_user.id)
    return perf


@router.put("/api/touches/{touch_id}/performances/{performance_id}", response_model=schemas.PerformanceRead)
def update_performance(
    touch_id: int,
    performance_id: int,
    perf_in: schemas.PerformanceUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    get_touch_or_404(touch_id, current_user, db)
    perf = get_performance_or_404(performance_id, touch_id, db)
    updated_fields = perf_in.model_dump(exclude_unset=True)
    log.debug("update_performance_request", performance_id=performance_id, touch_id=touch_id, user_id=current_user.id, updated_fields=updated_fields)
    for field, value in updated_fields.items():
        setattr(perf, field, value)
    db.commit()
    db.refresh(perf)
    log.info("performance_updated", performance_id=performance_id, touch_id=touch_id, fields=list(updated_fields.keys()), user_id=current_user.id)
    return perf


@router.delete("/api/touches/{touch_id}/performances/{performance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_performance(
    touch_id: int,
    performance_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    get_touch_or_404(touch_id, current_user, db)
    perf = get_performance_or_404(performance_id, touch_id, db)
    db.delete(perf)
    db.commit()
    log.info("performance_deleted", performance_id=performance_id, touch_id=touch_id, user_id=current_user.id)


@router.patch("/api/touches/{touch_id}/performances/reorder", response_model=list[schemas.PerformanceRead])
def reorder_performances(
    touch_id: int,
    reorders: List[schemas.PerformanceReorder],
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    get_touch_or_404(touch_id, current_user, db)
    log.debug(
        "reorder_performances_request",
        touch_id=touch_id,
        user_id=current_user.id,
        order=[{"id": r.id, "order_index": r.order_index} for r in reorders],
    )
    updated = []
    for item in reorders:
        perf = get_performance_or_404(item.id, touch_id, db)
        perf.order_index = item.order_index
        updated.append(perf)
    db.commit()
    for perf in updated:
        db.refresh(perf)
    log.info("performances_reordered", touch_id=touch_id, count=len(updated), user_id=current_user.id)
    return updated
