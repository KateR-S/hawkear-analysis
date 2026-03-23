import pathlib
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import get_current_user
from ..database import get_db
from ..services.parser import parse_method_file, detect_n_bells, separate_rounds_and_changes

router = APIRouter(prefix="/api/touches", tags=["touches"])

BACKEND_DIR = pathlib.Path(__file__).resolve().parent.parent
UPLOADS_DIR = BACKEND_DIR / "uploads"


def get_touch_or_404(touch_id: int, user: models.User, db: Session) -> models.Touch:
    touch = db.query(models.Touch).filter(
        models.Touch.id == touch_id, models.Touch.user_id == user.id
    ).first()
    if not touch:
        raise HTTPException(status_code=404, detail="Touch not found")
    return touch


@router.get("/", response_model=list[schemas.TouchRead])
def list_touches(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Touch).filter(models.Touch.user_id == current_user.id).all()


@router.post("/", response_model=schemas.TouchRead, status_code=status.HTTP_201_CREATED)
def create_touch(touch_in: schemas.TouchCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    touch = models.Touch(user_id=current_user.id, **touch_in.model_dump())
    db.add(touch)
    db.commit()
    db.refresh(touch)
    return touch


@router.get("/{touch_id}", response_model=schemas.TouchRead)
def get_touch(touch_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return get_touch_or_404(touch_id, current_user, db)


@router.put("/{touch_id}", response_model=schemas.TouchRead)
def update_touch(touch_id: int, touch_in: schemas.TouchUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    touch = get_touch_or_404(touch_id, current_user, db)
    for field, value in touch_in.model_dump(exclude_unset=True).items():
        setattr(touch, field, value)
    db.commit()
    db.refresh(touch)
    return touch


@router.delete("/{touch_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_touch(touch_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    touch = get_touch_or_404(touch_id, current_user, db)
    db.delete(touch)
    db.commit()


@router.post("/{touch_id}/method", response_model=schemas.TouchRead)
async def upload_method(touch_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    touch = get_touch_or_404(touch_id, current_user, db)
    content = (await file.read()).decode("utf-8")
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
    return touch
