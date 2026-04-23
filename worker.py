import os
from celery import Celery
from main import GitHubHelper

# Use Redis as the broker
app = Celery('llm_inference_task', broker=os.getenv('CELERY_BROKER_URL'))

# Celery uses RabbitMQ/Redis in backend. But it does all the system feature itself without coding manually

@app.task
def regenerate_doc(repo_url: str):
    helper=GitHubHelper()

    helper.delete_folder("./cloned-repos")
    helper.delete_folder("./chroma-store")
    
    helper.clone_repository(repo_url, "./cloned-repos")
    files=helper.walkRepo("./cloned-repos")
    files=helper.chunkFiles(files)
    helper.dbStore(files)
    response=helper.llm_query("Explain the architecture of the codebase")
    helper.post_to_wiki(response)

    return True