import pytest
import os
from fastapi.testclient import TestClient
from main import app

COSMOS_MODIFY_TOKEN = os.getenv("COSMOS_MODIFY_TOKEN")

client = TestClient(app)

# Global variable to store the blog post ID
created_blog_id = None

def test_create_blog_post():
    global created_blog_id
    response = client.post(
        "/blog/",
        headers={"Authorization": "Bearer " + COSMOS_MODIFY_TOKEN},
        data={
            "title": "Test Blog",
            "content": "This is a test blog content.",
            "author": "Test Author",
            "category": "Test Category"
        }
    )
    assert response.status_code == 200
    assert "id" in response.json()
    created_blog_id = response.json()["id"]
    assert response.json()["message"] == "Blog post created successfully"

def test_get_all_blog_posts():
    response = client.get("/blog/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_blog_post():
    global created_blog_id
    response = client.get(f"/blog/{created_blog_id}")
    if response.status_code == 200:
        assert "id" in response.json()
        assert response.json()["id"] == created_blog_id
    else:
        assert response.status_code == 404

def test_get_all_categories():
    response = client.get("/blog/categories/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_blog_posts_by_category():
    category = "Test Category"
    response = client.get(f"/blog/category/{category}")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_update_blog_post():
    global created_blog_id

    # Update the blog post
    response = client.put(
        f"/blog/{created_blog_id}",
        headers={"Authorization": "Bearer " + COSMOS_MODIFY_TOKEN},
        data={
            "title": "Updated Test Blog",
            "content": "This is updated test blog content.",
            "author": "Updated Test Author",
            "category": "Updated Test Category"
        }
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Blog post updated successfully"

    # Verify the update
    response = client.get(f"/blog/{created_blog_id}")
    assert response.status_code == 200
    blog_post = response.json()
    assert blog_post["title"] == "Updated Test Blog"
    assert blog_post["content"] == "This is updated test blog content."
    assert blog_post["author"] == "Updated Test Author"
    assert blog_post["category"] == "Updated Test Category"

def test_delete_blog_post():
    global created_blog_id
    response = client.delete(
        f"/blog/{created_blog_id}",
        headers={"Authorization": "Bearer " + COSMOS_MODIFY_TOKEN},
    )
    if response.status_code == 200:
        assert response.json()["message"] == "Blog post deleted successfully"
    else:
        assert response.status_code == 404
