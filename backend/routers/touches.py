import pathlib
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
import structlog

from .. import models, schemas
from ..auth import get_current_user
from ..database import get_db
from ..services.parser import parse_method_file, detect_n_bells, separate_rounds_and_changes

router = APIRouter(prefix="/api/touches", tags=["touches"])
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


@router.get("/", response_model=list[schemas.TouchRead])
def list_touches(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    touches = db.query(models.Touch).filter(models.Touch.user_id == current_user.id).all()
    log.debug(
        "touches_listed",
        user_id=current_user.id,
        count=len(touches),
        touch_ids=[t.id for t in touches],
        touch_names=[t.name for t in touches],
    )
    return touches


@router.post("/", response_model=schemas.TouchRead, status_code=status.HTTP_201_CREATED)
def create_touch(touch_in: schemas.TouchCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    log.debug("create_touch_request", user_id=current_user.id, request_body=touch_in.model_dump())
    touch = models.Touch(user_id=current_user.id, **touch_in.model_dump())
    db.add(touch)
    db.commit()
    db.refresh(touch)
    log.info(
        "touch_created",
        touch_id=touch.id,
        name=touch.name,
        user_id=current_user.id,
    )
    return touch


@router.get("/{touch_id}", response_model=schemas.TouchRead)
def get_touch(touch_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    touch = get_touch_or_404(touch_id, current_user, db)
    log.debug(
        "touch_fetched",
        touch_id=touch_id,
        user_id=current_user.id,
        name=touch.name,
        n_bells=touch.n_bells,
        rounds_rows=touch.rounds_rows,
        has_method_file=touch.method_file_path is not None,
    )
    return touch


@router.put("/{touch_id}", response_model=schemas.TouchRead)
def update_touch(touch_id: int, touch_in: schemas.TouchUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    touch = get_touch_or_404(touch_id, current_user, db)
    updated_fields = touch_in.model_dump(exclude_unset=True)
    log.debug("update_touch_request", touch_id=touch_id, user_id=current_user.id, updated_fields=updated_fields)
    for field, value in updated_fields.items():
        setattr(touch, field, value)
    db.commit()
    db.refresh(touch)
    log.info("touch_updated", touch_id=touch_id, fields=list(updated_fields.keys()), user_id=current_user.id)
    return touch


@router.delete("/{touch_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_touch(touch_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    touch = get_touch_or_404(touch_id, current_user, db)
    db.delete(touch)
    db.commit()
    log.info("touch_deleted", touch_id=touch_id, user_id=current_user.id)


@router.post("/{touch_id}/method", response_model=schemas.TouchRead)
async def upload_method(touch_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    touch = get_touch_or_404(touch_id, current_user, db)
    log.debug("method_upload_started", touch_id=touch_id, filename=file.filename, content_type=file.content_type, user_id=current_user.id)
    content = (await file.read()).decode("utf-8")
    log.debug("method_file_head", touch_id=touch_id, filename=file.filename, head=_head_lines(content))
    methods_dir = UPLOADS_DIR / "methods"
    methods_dir.mkdir(parents=True, exist_ok=True)
    file_path = methods_dir / f"{touch_id}.txt"
    file_path.write_text(content)
    rows = parse_method_file(content)
    if rows:
        n_bells = detect_n_bells(rows)
        rounds_end, _ = separate_rounds_and_changes(rows, n_bells)
        touch.method_file_path = str(file_path)
        touch.n_bells = n_bells
        touch.rounds_rows = rounds_end
    db.commit()
    db.refresh(touch)
    log.info(
        "method_uploaded",
        touch_id=touch_id,
        filename=file.filename,
        total_lines=len(content.splitlines()),
        n_bells=touch.n_bells,
        rounds_rows=touch.rounds_rows,
        user_id=current_user.id,
    )
    return touch
