from fastapi import FastAPI, UploadFile, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from azure.cosmos import CosmosClient
from uuid import uuid4
import os
import logging
from datetime import datetime, timezone
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Azure Cosmos DB configuration
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_MODIFY_TOKEN = os.getenv("COSMOS_MODIFY_TOKEN")
DATABASE_NAME = "BlogDatabase"
CONTAINER_NAME = "BlogPosts"

# Define a constant for error messages
BLOG_POST_NOT_FOUND = "Blog post not found"

client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
database = client.create_database_if_not_exists(DATABASE_NAME)
container = database.create_container_if_not_exists(
    id=CONTAINER_NAME,
    partition_key={"paths": ["/id"], "kind": "Hash"},
    offer_throughput=400
)

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    if token != COSMOS_MODIFY_TOKEN:
        logging.info(f"Invalid token provided: {token}")
        raise HTTPException(status_code=401, detail="Invalid request.")

class BlogPost(BaseModel):
    title: str
    content: str
    author: str
    category: str
    id: str | None = None
    date: str | None = None

@app.post("/blog/")
async def create_blog_post(
    blog_post: BlogPost,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token)
):
    blog_post = blog_post.model_copy(update={
        "id": str(uuid4()),
        "date": datetime.now(timezone.utc).isoformat()
    })
    container.create_item(body=blog_post.model_dump())
    logging.info(f"Created blog post with ID: {blog_post.id}")
    return {"message": "Blog post created successfully", "id": blog_post.id}

@app.get("/blog/{blog_id}")
async def get_blog_post(blog_id: str):
    query = f"SELECT * FROM c WHERE c.id = '{blog_id}'"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    if not items:
        return {"error": BLOG_POST_NOT_FOUND}
    return items[0]

@app.get("/blog/")
async def get_all_blog_posts():
    query = "SELECT c.id, c.category, c.title, c.author, c.date FROM c ORDER BY c.date DESC"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    return items

@app.get("/blog/categories/")
async def get_all_categories():
    query = "SELECT DISTINCT c.category FROM c"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    return [item["category"] for item in items]

@app.get("/blog/category/{category}")
async def get_blog_posts_by_category(category: str):
    query = f"SELECT c.id, c.title, c.author, c.date FROM c WHERE c.category = '{category}' ORDER BY c.date DESC"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    return items

@app.put("/blog/{blog_id}")
async def update_blog_post(
    blog_id: str,
    blog_post: BlogPost,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token)
):
    query = f"SELECT * FROM c WHERE c.id = '{blog_id}'"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    if not items:
        raise HTTPException(status_code=404, detail=BLOG_POST_NOT_FOUND)
    blog_post = blog_post.model_copy(update={
        "id": blog_id,
        "date": datetime.now(timezone.utc).isoformat()
    })
    container.upsert_item(body=blog_post.model_dump())
    return {"message": "Blog post updated successfully", "id": blog_id}

@app.delete("/blog/{blog_id}")
async def delete_blog_post(blog_id: str, credentials: HTTPAuthorizationCredentials = Depends(verify_token)):
    try:
        container.delete_item(item=blog_id, partition_key=blog_id)
        logging.info(f"Blog post deleted: {blog_id}")
        return {"message": "Blog post deleted successfully"}
    except Exception:
        raise HTTPException(status_code=404, detail=BLOG_POST_NOT_FOUND)
