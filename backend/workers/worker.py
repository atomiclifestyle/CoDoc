import os
from celery import Celery
from backend.main import GitHubHelper
from backend.utils.db_connect import db_manager

#Redis as the broker
app = Celery('llm_inference_task', broker=os.getenv('CELERY_BROKER_URL'))

@app.task
def regenerate_doc(repo_url: str, page_name: str):
    helper=GitHubHelper()
    response=helper.generate(repo_url, page_name)
    repos=db_manager.db.repos

    repo = repos.find_one({
        "repo_url": repo_url
    })

    if not repo:
        return False

    repos.update_one(
        {"repo_url": repo_url},
        {
            "$set": {
                "content": response,
            }
        }
    )

    return True
