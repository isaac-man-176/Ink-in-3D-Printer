from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api import convert, analyze
import os

app = FastAPI()

app.include_router(convert.router)
app.include_router(analyze.router)

# Serve static files (built frontend)
frontend_dist = os.path.join(os.path.dirname(__file__), "../frontend/dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")