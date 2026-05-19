import os
from celery import Celery
from main import GitHubHelper

# Use Redis as the broker
app = Celery('llm_inference_task', broker=os.getenv('CELERY_BROKER_URL'))

# Celery uses RabbitMQ/Redis in backend. But it does all the system feature itself without coding manually

@app.task
def regenerate_doc(repo_url: str, page_name: str):
    helper=GitHubHelper()
    helper.generate(repo_url, page_name)

    return True
