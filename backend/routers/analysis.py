import pathlib
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models
from ..auth import get_current_user
from ..database import get_db
from ..services.analysis import analyse_performance, analyse_multiple_performances
from ..services.characteristics import compute_characteristics

router = APIRouter(tags=["analysis"])

BACKEND_DIR = pathlib.Path(__file__).resolve().parent.parent


def get_touch_or_404(touch_id: int, user: models.User, db: Session) -> models.Touch:
    touch = db.query(models.Touch).filter(
        models.Touch.id == touch_id, models.Touch.user_id == user.id
    ).first()
    if not touch:
        raise HTTPException(status_code=404, detail="Touch not found")
    return touch


def load_method_content(touch: models.Touch) -> str:
    if not touch.method_file_path:
        raise HTTPException(status_code=400, detail="No method file uploaded for this touch")
    return pathlib.Path(touch.method_file_path).read_text()


def load_timing_content(perf: models.Performance) -> str:
    if not perf.timing_file_path:
        raise HTTPException(status_code=400, detail="No timing file for this performance")
    return pathlib.Path(perf.timing_file_path).read_text()


@router.get("/api/touches/{touch_id}/analysis")
def get_full_analysis(touch_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    touch = get_touch_or_404(touch_id, current_user, db)
    method_content = load_method_content(touch)
    perfs = db.query(models.Performance).filter(models.Performance.touch_id == touch_id).order_by(models.Performance.order_index).all()
    perf_list = []
    for p in perfs:
        if p.timing_file_path:
            perf_list.append({
                "label": p.label,
                "method_content": method_content,
                "timing_content": pathlib.Path(p.timing_file_path).read_text(),
            })
    if not perf_list:
        raise HTTPException(status_code=400, detail="No performances with timing data")
    return analyse_multiple_performances(perf_list)


@router.get("/api/touches/{touch_id}/analysis/{performance_id}")
def get_performance_analysis(touch_id: int, performance_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    touch = get_touch_or_404(touch_id, current_user, db)
    method_content = load_method_content(touch)
    perf = db.query(models.Performance).filter(
        models.Performance.id == performance_id,
        models.Performance.touch_id == touch_id,
    ).first()
    if not perf:
        raise HTTPException(status_code=404, detail="Performance not found")
    timing_content = load_timing_content(perf)
    return analyse_performance(method_content, timing_content)


@router.get("/api/touches/{touch_id}/analysis/{performance_id}/rounds")
def get_rounds_analysis(touch_id: int, performance_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    touch = get_touch_or_404(touch_id, current_user, db)
    method_content = load_method_content(touch)
    perf = db.query(models.Performance).filter(
        models.Performance.id == performance_id,
        models.Performance.touch_id == touch_id,
    ).first()
    if not perf:
        raise HTTPException(status_code=404, detail="Performance not found")
    timing_content = load_timing_content(perf)
    result = analyse_performance(method_content, timing_content)
    rounds_rows = result.get("rounds_rows", 0)
    striking_errors = result.get("striking_errors", [])
    return {
        "rounds_rows": rounds_rows,
        "striking_errors": striking_errors[:rounds_rows],
        "summary_stats": result.get("summary_stats"),
    }


@router.get("/api/touches/{touch_id}/analysis/{performance_id}/characteristics")
def get_characteristics(touch_id: int, performance_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    touch = get_touch_or_404(touch_id, current_user, db)
    method_content = load_method_content(touch)
    perf = db.query(models.Performance).filter(
        models.Performance.id == performance_id,
        models.Performance.touch_id == touch_id,
    ).first()
    if not perf:
        raise HTTPException(status_code=404, detail="Performance not found")
    timing_content = load_timing_content(perf)
    result = analyse_performance(method_content, timing_content)
    striking_errors = result.get("striking_errors", [])
    per_bell_errors: dict[int, list[float]] = {}
    for row_errors in striking_errors:
        for entry in row_errors:
            bell = entry["bell"]
            per_bell_errors.setdefault(bell, []).append(entry["error_ms"])
    return compute_characteristics(per_bell_errors)
