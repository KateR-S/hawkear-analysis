import pathlib
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import engine, Base
from .routers import auth, touches, performances, analysis


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    uploads_dir = pathlib.Path(__file__).resolve().parent / "uploads"
    uploads_dir.mkdir(exist_ok=True)
    yield


app = FastAPI(title="Hawkear Analysis API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(touches.router)
app.include_router(performances.router)
app.include_router(analysis.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


frontend_dist = pathlib.Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")
