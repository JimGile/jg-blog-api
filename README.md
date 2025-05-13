# Blog API with FastAPI

This project is a FastAPI-based backend for a blog application. It integrates with Azure Cosmos DB to store blog entries and supports image uploads. The API is designed to be deployable as an Azure Function.

## Features
- CRUD operations for blog posts.
- Markdown support for blog content.
- Image upload and storage.
- Integration with Azure Cosmos DB.
- Deployable as an Azure Function.

## Requirements
- Python 3.9+
- FastAPI
- Azure SDK for Python
- Azure Functions Core Tools

## Setup
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application locally:
   ```bash
   uvicorn main:app --reload
   ```

## Deployment
To deploy as an Azure Function, follow these steps:
1. Install Azure Functions Core Tools.
2. Deploy using the Azure CLI:
   ```bash
   func azure functionapp publish <FunctionAppName>
   ```
