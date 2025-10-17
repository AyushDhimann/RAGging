"""
Recreate Qdrant collection with correct settings
"""
import requests
import time

print("Deleting existing collection...")
response = requests.delete("http://localhost:6333/collections/multilingual_docs")
print(f"Delete response: {response.status_code}")

time.sleep(2)

print("\nCreating new collection with optimized settings...")
response = requests.put(
    "http://localhost:6333/collections/multilingual_docs",
    json={
        "vectors": {
            "size": 768,
            "distance": "Cosine"
        },
        "optimizers_config": {
            "indexing_threshold": 50  # Low threshold for immediate indexing
        }
    }
)

if response.status_code == 200:
    print("[OK] Collection created successfully")
    print("\nSettings:")
    print("  - Vector size: 768")
    print("  - Distance: Cosine")
    print("  - Indexing threshold: 50")
    print("\nCollection is ready for ingestion!")
else:
    print(f"ERROR: {response.status_code} - {response.text}")

