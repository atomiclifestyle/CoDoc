import os
import hmac
import hashlib
from datetime import datetime, timezone
from dotenv import load_dotenv

from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware

from authlib.integrations.starlette_client import OAuth

from backend.workers.worker import regenerate_doc
from backend.utils.db_connect import db_manager

load_dotenv() 

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
SESSION_SECRET = os.getenv("SESSION_SECRET")

FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://localhost:3000"
)

GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    uri = os.getenv("MONGODB_URI")
    print("MONGODB URI:", uri.split("@")[-1] if uri else None)
    db_manager.connect(
        uri,
        "codoc"
    )

    print("DATABASE:", db_manager.db.name)
    print("COLLECTIONS:", db_manager.db.list_collection_names())

    yield

    db_manager.disconnect()


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="lax",
    https_only=False,  # True in production
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth = OAuth()

oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url=(
        "https://accounts.google.com/.well-known/openid-configuration"
    ),
    client_kwargs={
        "scope": "openid email profile"
    },
)

async def get_current_user(request: Request):

    user = request.session.get("user")

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )

    return user

@app.get("/auth/login")
async def google_login(request: Request):

    redirect_uri = request.url_for("google_callback")

    return await oauth.google.authorize_redirect(
        request,
        redirect_uri
    )

@app.get("/auth/callback")
async def google_callback(request: Request):

    try:
        token = await oauth.google.authorize_access_token(request)

        # Authlib/OpenID Connect gives us the user information
        user_info = token.get("userinfo")

        if not user_info:
            user_info = await oauth.google.userinfo(
                token=token
            )

    except Exception as e:
        print("Google OAuth error:", e)

        raise HTTPException(
            status_code=401,
            detail="Google authentication failed"
        )

    google_id = user_info["sub"]
    email = user_info["email"]

    first_name = user_info.get(
        "given_name",
        user_info.get("name", "")
    )

    users = db_manager.db.users

    # Create user if they don't exist
    users.update_one(
        {"google_id": google_id},
        {
            "$set": {
                "email": email,
                "first_name": first_name,
                "updated_at": datetime.now(timezone.utc),
            },
            "$setOnInsert": {
                "google_id": google_id,
                "repos": [],
                "created_at": datetime.now(timezone.utc),
            }
        },
        upsert=True
    )

    # Store only the necessary identity information
    request.session["user"] = {
        "google_id": google_id,
        "email": email,
        "first_name": first_name,
    }

    return RedirectResponse(
        url=FRONTEND_URL
    )

@app.post("/auth/logout")
async def logout(request: Request):

    request.session.clear()

    return {
        "status": "success",
        "message": "Logged out"
    }

@app.get("/auth/me")
async def get_me(request: Request):
    print("SESSION:", request.session)
    print("COOKIES:", request.cookies)

    user = await get_current_user(request)

    return user

def verify_github_signature(
    payload: bytes,
    signature: str | None
) -> bool:

    if not GITHUB_WEBHOOK_SECRET:
        return False

    if not signature:
        return False

    expected_signature = hmac.new(
        GITHUB_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    expected_signature = f"sha256={expected_signature}"

    return hmac.compare_digest(
        expected_signature,
        signature
    )

@app.post("/webhook")
async def process_webhook(request: Request):

    body = await request.body()

    signature = request.headers.get(
        "X-Hub-Signature-256"
    )

    if not verify_github_signature(
        body,
        signature
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid webhook signature"
        )

    payload = await request.json()

    event = request.headers.get(
        "X-GitHub-Event"
    )

    # Only process pull request events
    if event != "pull_request":
        return {
            "status": "Ignored",
            "message": "Not a pull request event"
        }

    action = payload.get("action")

    # Only regenerate when PR is merged
    if action != "closed":
        return {
            "status": "Ignored",
            "message": "Pull request is not closed"
        }

    pull_request = payload.get(
        "pull_request",
        {}
    )

    is_merged = pull_request.get(
        "merged",
        False
    )

    repo_url = payload.get(
        "repository",
        {}
    ).get("clone_url")

    if not is_merged or not repo_url:
        return {
            "status": "Ignored",
            "message": "Pull request was not merged"
        }

    repos = db_manager.db.repos

    repo = repos.find_one({
        "repo_url": repo_url
    })

    if not repo:
        return {
            "status": "Ignored",
            "message": "Repository is not registered"
        }

    page_name = repo.get("page_name")

    regenerate_doc.delay(
        repo_url,
        page_name
    )

    return {
        "status": "Accepted",
        "message": "Document generation started"
    }

@app.get("/repo")
async def get_repos(request: Request):
    user = await get_current_user(request)
    print("DATABASE:", db_manager.db.name)
    print("COLLECTIONS:", db_manager.db.list_collection_names())
    users = db_manager.db.users

    # Fetch the record that actually has populated repos
    db_user = users.find_one({
        "google_id": user["google_id"],
    })

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    repos = db_user.get("repos", [])

    return {
        "name": db_user.get("first_name"),
        "repos": repos,
        "count": len(repos),
        "email": db_user.get("email")
    }

@app.post("/repo")
async def register_repo(
    request: Request
):

    user = await get_current_user(request)

    payload = await request.json()

    repo_url = payload.get("repo_url")
    page_name = payload.get("page_name")

    if not repo_url or not page_name:
        raise HTTPException(
            status_code=400,
            detail="repo_url and page_name are required"
        )

    repos = db_manager.db.repos
    users = db_manager.db.users

    # Check whether repository already exists
    existing_repo = repos.find_one({
        "repo_url": repo_url
    })

    if existing_repo:
        raise HTTPException(
            status_code=409,
            detail="Repository already registered"
        )

    repo = {
        "repo_url": repo_url,
        "page_name": page_name,
        "can_update_wiki": payload.get(
            "can_update_wiki",
            False
        ),
        "created_at": datetime.now(timezone.utc),
        "content": "",
        "google_id": user["google_id"],
    }

    repos.insert_one(repo)

    users.update_one(
        {
            "google_id": user["google_id"]
        },
        {
            "$push": {
                "repos": {
                    "repo_url": repo_url,
                    "page_name": page_name,
                    "can_update_wiki": repo["can_update_wiki"],
                }
            }
        }
    )

    regenerate_doc.delay(
        repo_url,
        page_name
    )

    return {
        "status": "success",
        "repo": {
            "repo_url": repo_url,
            "page_name": page_name,
        }
    }

@app.get("/doc")
async def get_latest_doc(
    request: Request,
    repo_url: str = Query(...)
):

    user = await get_current_user(request)

    repos = db_manager.db.repos

    repo = repos.find_one({
        "repo_url": repo_url,
        "google_id": user["google_id"],
    })

    if not repo:
        raise HTTPException(
            status_code=404,
            detail="Repository not found"
        )

    return {
        "repo_url": repo["repo_url"],
        "page_name": repo["page_name"],
        "content": repo.get("content", ""),
        "updated_at": repo.get("updated_at"),
    }

@app.post("/auth/demo-login")
async def demo_login(
    request: Request,
    email: str,
    password: str
):
    demo_email = os.getenv("DEMO_EMAIL")
    demo_password = os.getenv("DEMO_PASSWORD")

    print(demo_email)
    print(demo_password)

    if email != "demo@codoc.dev" or password != "demo-pass":
        raise HTTPException(
            status_code=401,
            detail="Invalid demo credentials"
        )

    users = db_manager.db.users

    # Use a fixed internal ID for the demo account
    demo_google_id = "demo-user"

    users.update_one(
        {"google_id": demo_google_id},
        {
            "$set": {
                "email": demo_email,
                "first_name": "Demo",
                "updated_at": datetime.now(timezone.utc),
            },
            "$setOnInsert": {
                "google_id": demo_google_id,
                "repos": [],
                "created_at": datetime.now(timezone.utc),
            }
        },
        upsert=True
    )

    request.session["user"] = {
        "google_id": demo_google_id,
        "email": "demo@codoc.dev",
        "first_name": "Demo",
        "is_demo": True,
    }

    return {
        "status": "success",
        "message": "Demo login successful"
    }