import os
from celery import Celery
from main import GitHubHelper

#Redis as the broker
app = Celery('llm_inference_task', broker=os.getenv('CELERY_BROKER_URL'))

@app.task
def regenerate_doc(repo_url: str, page_name: str):
    helper=GitHubHelper()
    helper.generate(repo_url, page_name)

    return True
