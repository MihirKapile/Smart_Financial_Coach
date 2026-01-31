import os
import pandas as pd
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.lancedb import LanceDb
from agno.knowledge.embedder.huggingface import HuggingfaceCustomEmbedder

hf_embedder = HuggingfaceCustomEmbedder(
    id="sentence-transformers/all-MiniLM-L6-v2",
    dimensions=384,
    api_key=os.getenv("HF_TOKEN")
)

vector_db = LanceDb(
    table_name="finance_vault",
    uri="tmp/lancedb",
    embedder=hf_embedder,
)



def get_knowledge_base():
    """Returns the unified Knowledge container."""
    return Knowledge(vector_db=vector_db)

def ingest_data(kb, file_path, file_type):
    """
    Ingests different file types into the LanceDB vector store.
    """
    if file_type in ['xlsx', 'xls']:
        df = pd.read_excel(file_path)
        csv_path = file_path.rsplit('.', 1)[0] + ".csv"
        df.to_csv(csv_path, index=False)
        kb.insert(path=csv_path)
    
    elif file_type == 'csv':
        kb.insert(path=file_path)
        
    elif file_type == 'pdf':
        kb.insert(path=file_path)