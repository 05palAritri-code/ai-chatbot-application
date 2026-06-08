import inspect
from ingest import get_vector_store

vector_store = get_vector_store()

print(inspect.signature(vector_store.delete))