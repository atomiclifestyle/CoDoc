from fastapi import FastAPI,Request
from worker import regenerate_doc

app=FastAPI()

@app.post("/webhook")
async def process_webhook(req: Request):
    payload=req.json()

    is_merged = payload.get("pull_request", {}).get("merged", False)
    repo_url = payload.get("repository", {}).get("clone_url")

    if is_merged and repo_url:
        regenerate_doc.delay(repo_url)
        return {"status": "Accepted", "message": "Document generation started"}

    return {"status": "Ignored", "message": "Documentation aborted"}