import streamlit as st
import subprocess
from pathlib import Path

from main import GitHubHelper
from app.utils.db_connect import db_manager

def delete_folder(path: str):
    path = Path(path)
    if path.exists():
        subprocess.run(
            ["cmd", "/c", "rmdir", "/s", "/q", str(path)],
            check=False
        )

def store_to_db(repo_url, page_name):
    # TODO: Connect db_manager in the Streamlit process before using db_manager.db.
    # The FastAPI lifespan connection does not initialize this separate app.
    repo_model=db_manager.db.repos
    repo_model.insert_one({
        "repo_url": repo_url,
        "page_name": page_name,
    })

def repo_name_parser(repo_url):
    repo_url=repo_url[:-4] if repo_url.endswith(".git") else repo_url
    repo_url=repo_url[19:] if repo_url.startswith("https://github.com/") else repo_url
    repo_url=repo_url[23:] if repo_url.startswith("https://www.github.com/") else repo_url

    return repo_url
    

st.title("Github Repository Analyser")
st.write("Analyse any codebase")

url=st.text_input("Github Repository URL", placeholder="https://github.com/...")
page_name=st.text_input("Preferred Github Wiki Page Name", placeholder="Architecture_Overview")

if st.button("Analyse"):
    if not url.strip():
        st.warning("Please enter the url")
    else:
        try:
            with st.spinner("Wait for it..."):
                # delete_folder("./cloned-repos")
                # delete_folder("./chroma-store")
                
                helper=GitHubHelper()
                response=helper.generate(url, page_name)
                store_to_db(url,page_name)

            st.success("Analysis completed")
            st.write(response)

        except Exception as e:
            st.error(e)
