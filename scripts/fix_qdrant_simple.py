"""
Fix Qdrant indexing using REST API directly
"""
import requests
import time

# Update optimizer config
print("Updating Qdrant optimizer config...")
response = requests.patch(
    "http://localhost:6333/collections/multilingual_docs",
    json={
        "optimizer_config": {
            "indexing_threshold": 100
        }
    }
)

if response.status_code == 200:
    print("[OK] Successfully updated optimizer config")
    print("Waiting 10 seconds for indexing to complete...")
    time.sleep(10)
    
    # Check status
    response = requests.get("http://localhost:6333/collections/multilingual_docs")
    data = response.json()
    
    indexed = data["result"]["indexed_vectors_count"]
    total = data["result"]["points_count"]
    
    print(f"Status: {indexed}/{total} vectors indexed")
    
    if indexed > 0:
        print(f"SUCCESS! Vectors are now indexed and searchable")
    else:
        print("Still indexing, may need a few more seconds...")
else:
    print(f"ERROR: {response.status_code} - {response.text}")

