import os
from sentence_transformers import SentenceTransformer
if __name__ == "__main__":
    models_cache_dir = os.getenv('MODELS_CACHE')
    os.makedirs(models_cache_dir, exist_ok=True)
    SentenceTransformer('sentence-transformers/LaBSE', cache_folder=models_cache_dir)
