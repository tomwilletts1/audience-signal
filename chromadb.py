# ChromaDB configuration
# Use environment variables for sensitive data
import os
import chromadb

# Get credentials from environment variables
api_key = os.getenv('CHROMADB_API_KEY')
tenant = os.getenv('CHROMADB_TENANT')
database = os.getenv('CHROMADB_DATABASE', 'Audience Signal')

if api_key and tenant:
    client = chromadb.CloudClient(
        api_key=api_key,
        tenant=tenant,
        database=database
    )
else:
    # Fallback to local ChromaDB if cloud credentials not provided
    client = chromadb.Client()
