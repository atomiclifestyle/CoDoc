import streamlit as st
from main import GitHubHelper
import subprocess
from pathlib import Path

def delete_folder(path: str):
    path = Path(path)
    if path.exists():
        subprocess.run(
            ["cmd", "/c", "rmdir", "/s", "/q", str(path)],
            check=False
        )

st.title("Github Repository Analyser")
st.write("Analyse any codebase")

url=st.text_input("Github Repository URL", placeholder="https://github.com/...")
page_name=st.text_input("Preferred Github Wiki Page Name", placeholder="Architecture_Overview")

if st.button("Analyse"):
    if url is None:
        st.warning("Please enter the url")
    else:
        try:
            with st.spinner("Wait for it..."):
                # delete_folder("./cloned-repos")
                # delete_folder("./chroma-store")
                
                helper=GitHubHelper()
                helper.clone_repository(url, "./cloned-repos")
                files=helper.walkRepo("./cloned-repos")
                files=helper.chunkFiles(files)
                helper.dbStore(files)
                response=helper.llm_query("Explain the architecture of the codebase")
                helper.post_to_wiki(response, page_name)

            st.success("Analysis completed")
            st.write(response)

        except Exception as e:
            st.error(e)
