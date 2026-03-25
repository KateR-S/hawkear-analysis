import pathlib
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import structlog

from .. import models
from ..auth import get_current_user
from ..database import get_db
from ..services.analysis import analyse_performance, analyse_multiple_performances
from ..services.characteristics import compute_characteristics

router = APIRouter(tags=["analysis"])
log = structlog.get_logger(__name__)

BACKEND_DIR = pathlib.Path(__file__).resolve().parent.parent

_FILE_HEAD_LINES = 5


def _head_lines(text: str, n: int = _FILE_HEAD_LINES) -> str:
    """Return the first *n* lines of *text* for debug logging."""
    lines = text.splitlines()
    head = "\n".join(lines[:n])
    if len(lines) > n:
        head += f"\n… ({len(lines) - n} more lines)"
    return head


def _analysis_head(result: dict) -> dict:
    """Return a concise debug summary of an analysis result dict."""
    summary = {}
    if "summary_stats" in result:
        summary["summary_stats"] = result["summary_stats"]
    if "striking_errors" in result:
        errors = result["striking_errors"]
        summary["striking_errors_total_rows"] = len(errors)
        summary["striking_errors_head"] = errors[:3]
    if "rounds_rows" in result:
        summary["rounds_rows"] = result["rounds_rows"]
    return summary


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
    log.debug("full_analysis_requested", touch_id=touch_id, user_id=current_user.id)
    touch = get_touch_or_404(touch_id, current_user, db)
    method_content = load_method_content(touch)
    log.debug("method_file_head", touch_id=touch_id, head=_head_lines(method_content))
    perfs = db.query(models.Performance).filter(models.Performance.touch_id == touch_id).order_by(models.Performance.order_index).all()
    perf_list = []
    for p in perfs:
        if p.timing_file_path:
            timing_content = pathlib.Path(p.timing_file_path).read_text()
            log.debug(
                "timing_file_head",
                touch_id=touch_id,
                performance_id=p.id,
                label=p.label,
                total_lines=len(timing_content.splitlines()),
                head=_head_lines(timing_content),
            )
            perf_list.append({
                "label": p.label,
                "method_content": method_content,
                "timing_content": timing_content,
            })
    if not perf_list:
        log.debug("full_analysis_no_performances", touch_id=touch_id, user_id=current_user.id)
        return {"performances": [], "trend": {}}
    result = analyse_multiple_performances(perf_list)
    first_perf = result.get("performances", [{}])[0] if result.get("performances") else {}
    log.debug("full_analysis_result_head", touch_id=touch_id, result_head=_analysis_head(first_perf))
    log.info("full_analysis_complete", touch_id=touch_id, performance_count=len(perf_list), user_id=current_user.id)
    return result


@router.get("/api/touches/{touch_id}/analysis/{performance_id}")
def get_performance_analysis(touch_id: int, performance_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    log.debug("performance_analysis_requested", touch_id=touch_id, performance_id=performance_id, user_id=current_user.id)
    touch = get_touch_or_404(touch_id, current_user, db)
    method_content = load_method_content(touch)
    log.debug("method_file_head", touch_id=touch_id, performance_id=performance_id, head=_head_lines(method_content))
    perf = db.query(models.Performance).filter(
        models.Performance.id == performance_id,
        models.Performance.touch_id == touch_id,
    ).first()
    if not perf:
        raise HTTPException(status_code=404, detail="Performance not found")
    timing_content = load_timing_content(perf)
    log.debug(
        "timing_file_head",
        touch_id=touch_id,
        performance_id=performance_id,
        total_lines=len(timing_content.splitlines()),
        head=_head_lines(timing_content),
    )
    result = analyse_performance(method_content, timing_content)
    log.debug("performance_analysis_result_head", touch_id=touch_id, performance_id=performance_id, result_head=_analysis_head(result))
    log.info("performance_analysis_complete", touch_id=touch_id, performance_id=performance_id, user_id=current_user.id)
    return result


@router.get("/api/touches/{touch_id}/analysis/{performance_id}/rounds")
def get_rounds_analysis(touch_id: int, performance_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    log.debug("rounds_analysis_requested", touch_id=touch_id, performance_id=performance_id, user_id=current_user.id)
    touch = get_touch_or_404(touch_id, current_user, db)
    method_content = load_method_content(touch)
    log.debug("method_file_head", touch_id=touch_id, performance_id=performance_id, head=_head_lines(method_content))
    perf = db.query(models.Performance).filter(
        models.Performance.id == performance_id,
        models.Performance.touch_id == touch_id,
    ).first()
    if not perf:
        raise HTTPException(status_code=404, detail="Performance not found")
    timing_content = load_timing_content(perf)
    log.debug(
        "timing_file_head",
        touch_id=touch_id,
        performance_id=performance_id,
        total_lines=len(timing_content.splitlines()),
        head=_head_lines(timing_content),
    )
    result = analyse_performance(method_content, timing_content)
    rounds_rows = result.get("rounds_rows", 0)
    striking_errors = result.get("striking_errors", [])
    response = {
        "rounds_rows": rounds_rows,
        "striking_errors": striking_errors[:rounds_rows],
        "summary_stats": result.get("summary_stats"),
    }
    log.debug(
        "rounds_analysis_result_head",
        touch_id=touch_id,
        performance_id=performance_id,
        rounds_rows=rounds_rows,
        summary_stats=response["summary_stats"],
        striking_errors_head=striking_errors[:3],
    )
    log.info("rounds_analysis_complete", touch_id=touch_id, performance_id=performance_id, rounds_rows=rounds_rows, user_id=current_user.id)
    return response


@router.get("/api/touches/{touch_id}/analysis/{performance_id}/characteristics")
def get_characteristics(touch_id: int, performance_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    log.debug("characteristics_requested", touch_id=touch_id, performance_id=performance_id, user_id=current_user.id)
    touch = get_touch_or_404(touch_id, current_user, db)
    method_content = load_method_content(touch)
    log.debug("method_file_head", touch_id=touch_id, performance_id=performance_id, head=_head_lines(method_content))
    perf = db.query(models.Performance).filter(
        models.Performance.id == performance_id,
        models.Performance.touch_id == touch_id,
    ).first()
    if not perf:
        raise HTTPException(status_code=404, detail="Performance not found")
    timing_content = load_timing_content(perf)
    log.debug(
        "timing_file_head",
        touch_id=touch_id,
        performance_id=performance_id,
        total_lines=len(timing_content.splitlines()),
        head=_head_lines(timing_content),
    )
    result = analyse_performance(method_content, timing_content)
    striking_errors = result.get("striking_errors", [])
    per_bell_errors: dict[int, list[float]] = {}
    for row_errors in striking_errors:
        for entry in row_errors:
            bell = entry["bell"]
            per_bell_errors.setdefault(bell, []).append(entry["error_ms"])
    log.debug(
        "per_bell_errors_head",
        touch_id=touch_id,
        performance_id=performance_id,
        bell_count=len(per_bell_errors),
        head={str(k): v[:5] for k, v in list(per_bell_errors.items())[:4]},
    )
    characteristics = compute_characteristics(per_bell_errors)
    log.debug(
        "characteristics_result_head",
        touch_id=touch_id,
        performance_id=performance_id,
        characteristics_head=dict(list(characteristics.items())[:4]) if isinstance(characteristics, dict) else list(characteristics)[:4],
    )
    log.info("characteristics_complete", touch_id=touch_id, performance_id=performance_id, bell_count=len(per_bell_errors), user_id=current_user.id)
    return characteristics
