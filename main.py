from fastapi import FastAPI, UploadFile, Form, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from azure.cosmos import CosmosClient
from uuid import uuid4
import os
from datetime import datetime, timezone

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
        raise HTTPException(status_code=401, detail="Invalid request.")

@app.post("/blog/")
async def create_blog_post(
    title: str = Form(...),
    content: str = Form(...),
    author: str = Form(...),
    category: str = Form(...),
    image: UploadFile = None,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token)
):
    blog_id = str(uuid4())
    blog_post = {
        "id": blog_id,
        "category": category,
        "title": title,
        "content": content,
        "author": author,
        "date": datetime.now(timezone.utc).isoformat(),
        "image_url": None
    }

    if image:
        image_path = f"images/{blog_id}_{image.filename}"
        with open(image_path, "wb") as f:
            f.write(await image.read())
        blog_post["image_url"] = image_path

    container.create_item(body=blog_post)
    print(f"Created blog post with ID: {blog_id}")
    return {"message": "Blog post created successfully", "id": blog_id}

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
    title: str = Form(None),
    content: str = Form(None),
    author: str = Form(None),
    category: str = Form(None),
    image: UploadFile = None,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token)
):
    query = f"SELECT * FROM c WHERE c.id = '{blog_id}'"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))

    if not items:
        raise HTTPException(status_code=404, detail=BLOG_POST_NOT_FOUND)

    blog_post = items[0]

    if title:
        blog_post["title"] = title
    if content:
        blog_post["content"] = content
    if author:
        blog_post["author"] = author
    if category:
        blog_post["category"] = category

    if image:
        image_path = f"images/{blog_id}_{image.filename}"
        with open(image_path, "wb") as f:
            f.write(await image.read())
        blog_post["image_url"] = image_path

    blog_post["date"] = datetime.now(timezone.utc).isoformat()

    container.upsert_item(body=blog_post)
    return {"message": "Blog post updated successfully", "id": blog_id}

@app.delete("/blog/{blog_id}")
async def delete_blog_post(blog_id: str, credentials: HTTPAuthorizationCredentials = Depends(verify_token)):
    try:
        container.delete_item(item=blog_id, partition_key=blog_id)
        return {"message": "Blog post deleted successfully"}
    except Exception:
        raise HTTPException(status_code=404, detail=BLOG_POST_NOT_FOUND)
