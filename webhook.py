import os
import datetime
from fastapi import FastAPI,Request
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

from worker import regenerate_doc
from database import db_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    db_manager.connect(os.getenv('MONGODB_URI'), "codoc_db")
    yield

    db_manager.disconnect()

app=FastAPI(lifespan=lifespan)

@dataclass
class RepoModel:
    repo_url: str
    page_name: str
    can_update_wiki: bool
    created_at: datetime = datetime.now()

    def to_dict(self):
        return asdict(self)

@app.post("/webhook")
async def process_webhook(req: Request):
    payload=await req.json()
    repo_model=db_manager.db.repos

    is_merged=payload.get("pull_request", {}).get("merged", False)
    repo_url=payload.get("repository", {}).get("clone_url")

    if is_merged and repo_url:
        repo=repo_model.find_one({"repo_url": repo_url})
        if repo:
            regenerate_doc.delay(repo_url, repo.get("page_name"))
            return {"status": "Accepted", "message": "Document generation started"}

    return {"status": "Ignored", "message": "Documentation aborted"}
