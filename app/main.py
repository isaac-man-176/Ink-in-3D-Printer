from fastapi import FastAPI
from app.api import convert, analyze

app = FastAPI()

app.include_router(convert.router)
app.include_router(analyze.router)