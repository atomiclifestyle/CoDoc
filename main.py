import os
os.environ["CHROMA_TELEMETRY"] = "false"
from git import Repo
from pathlib import Path
import subprocess
import ollama 
import chromadb
import shutil
from chromadb.config import Settings
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from datetime import datetime

SKIP_FILES = {
    "package-lock.json", 
    "vercel.json", 
    ".gitignore"
}

SKIP_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",  # images
    ".mp4", ".mp3", ".wav",                            # media
    ".zip", ".tar", ".gz",                             # archives
    ".pdf", ".docx",                                   # docs
    ".lock",                                           # lock files
    ".pyc", ".pyo",                                    # python cache
    ".exe", ".bin", ".so", ".dylib",                   # binaries
    ".gitignore",
    ".github"
}

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".github",
    ".venv", "venv", "env",
    "dist", "build", ".next",
    ".idea", ".vscode"
}

class GitHubHelper:

    def __init__(self):
        self.delete_folder("./chroma-store")
        self.repo=None
        self.client = chromadb.PersistentClient(path="./chroma-store")
        self.collection = self.client.get_or_create_collection(name="docs")
    
    def clone_repository(self,remote_url,target_dir):
        self.delete_folder(target_dir)
        self.repo_url=remote_url[:-4] if remote_url.endswith(".git") else remote_url
        self.repo=Repo.clone_from(remote_url,target_dir)
        assert not self.repo.bare
        print(f"Cloned Successfull to {target_dir}")
        
    def walkRepo(self,target_dir):
        root_dir=Path(target_dir)
        files=[]
        for file_path in root_dir.rglob("*"):
            if(file_path.is_file()):
                print(f"Reading :{file_path}")
                try: 
                    if file_path.name in SKIP_FILES:
                        continue
                    if any(part in SKIP_DIRS for part in file_path.parts):
                        continue
                    if file_path.suffix.lower() in SKIP_EXTENSIONS:
                        continue
                    content=file_path.read_text(encoding='utf-8')
                    if not content.strip():
                        continue
                    files.append({
                    "path": str(file_path.relative_to(root_dir)),
                    "content": content,
                    "extension": file_path.suffix.lower(),
                    "size": file_path.stat().st_size,
                    })

                except Exception as e:
                    print(f"Could not read {file_path}:{e}")
        return files
    
    def dbStore(self,files):
        print("Embedding and storing in ChromaDB...")
        for file in files:
            print(f"Embedding {file['path']}...")
            response=ollama.embed(model='nomic-embed-text',input=file["content"])

            unique_id = f"{file['path']}_chunk_{file['chunk_index']}"

            self.collection.upsert(
                ids=[unique_id],
                embeddings=[response["embeddings"][0]],
                documents=[file["content"]],
                metadatas=[{
                    "path": file["path"],
                    "extension": file["extension"],
                }]
            )

        print(f"Stored {len(files)} files in ChromaDB.")
    
    def chunkFiles(self,files):
        EXTENSION_MAP = {
        ".py": Language.PYTHON,
        ".js": Language.JS,
        ".ts": Language.TS,
        ".jsx": Language.JS,
        ".tsx": Language.TS,
        ".go": Language.GO,
        ".java": Language.JAVA,
        ".rb": Language.RUBY,
        ".rs": Language.RUST,
        ".cpp": Language.CPP,
        ".c": Language.C,
        ".cs": Language.CSHARP,
        ".md": Language.MARKDOWN,
        ".html": Language.HTML,
        }
        all_chunks=[]
        for file in files:
            ext=file['extension']
            language=EXTENSION_MAP.get(ext)
            if language:
                splitter=RecursiveCharacterTextSplitter.from_language(
                    language=language,
                    chunk_size=1000,
                    chunk_overlap=100,
                )
            else:
                splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=100,
                )
            chunks=splitter.split_text(file["content"])
            for idx, chunk in enumerate(chunks):
                all_chunks.append({
                    "content":chunk,
                    "path":file["path"],
                    "extension":ext,
                    "chunk_index": idx
                })
        return all_chunks
    
    def llm_query(self, query: str):
        print("sending query to the llm")

        query_embed = ollama.embed(model='nomic-embed-text', input=query)
        query_embedding = query_embed["embeddings"][0]

        #query relevant data
        result = self.collection.query(
            query_embeddings=query_embedding,
            n_results=10
        )

        docs = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]

        context = []
        for doc,meta in zip(docs, metadatas):
            context.append(f"File: {meta['path']} - \n{doc}")

        context_str = "\n\n".join(context)
        if not context_str:
            return "Couldn't find relavant information for your query"
        
        llm = ChatOllama(model="qwen2.5-coder:1.5b", temperature=0)

        #construct prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a senior software engineer explaining a codebase. "
                       "Use the following codebase context to answer the user's question. "
                       "If the answer is not in the context, explicitly state that you don't know based on the provided code. "
                       "Always format code snippets clearly.\n\n"
                       "Context:\n{context}"),
            ("user", "{input}")
        ])

        chain = prompt | llm | StrOutputParser()

        response = chain.invoke({
            "context": context_str,
            "input": query
        })

        return response
    
    def post_to_wiki(self, response, base_page_name="Architecture_Overview"):
        current_date = datetime.now().strftime("%Y-%m-%d")
        page_name = f"{base_page_name}_{current_date}.md"
        wiki_url=f"{self.repo_url}.wiki.git"
        wiki_dir="./cloned-wiki"
        
        self.delete_folder(wiki_dir)
        wiki_repo=Repo.clone_from(wiki_url,wiki_dir)

        file_path=os.path.join(wiki_dir, page_name)

        with open(file_path, "w", encoding="utf-8") as file:
            file.write(response)

        wiki_repo.index.add([page_name])
        wiki_repo.index.commit(f"docs: auto-generated {page_name} by CoDoc")
        wiki_repo.remotes.origin.push()

        return

    def delete_folder(self, path: str):
        folder = Path(path)
        if folder.exists() and folder.is_dir():
            try:
                shutil.rmtree(folder)
            except Exception as e:
                print(f"Warning: Failed to delete {path} via shutil: {e}")

    def generate(self, repo_url, page_name):
        self.delete_folder("./cloned-repos")
        
        self.clone_repository(repo_url, "./cloned-repos")
        files=self.walkRepo("./cloned-repos")
        files=self.chunkFiles(files)
        self.dbStore(files)
        response=self.llm_query("Explain the architecture of the codebase, and list the tech stack used")
        self.post_to_wiki(response, page_name)

        return response
