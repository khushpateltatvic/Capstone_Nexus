try:
    print("Testing pinecone import...")
    from pinecone import Pinecone, ServerlessSpec
    print("Success!")
except Exception as e:
    print(f"Failed with exception: {e}")
except ImportError as e:
    print(f"Failed with ImportError: {e}")
