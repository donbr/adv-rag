# %% [markdown]
# # Postgres Data Analysis Queries

# %%
import os
import pandas as pd
from sqlalchemy import create_engine, text
from langchain_core.documents import Document
from dotenv import load_dotenv

# %%
POSTGRES_USER = "langchain"
POSTGRES_PASSWORD = "langchain"
POSTGRES_HOST = "localhost"
POSTGRES_PORT = "6024"
POSTGRES_DB = "langchain"

# %%
# Construct the synchronous database connection string for SQLAlchemy
sync_conn_str = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
    f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

# Create a SQLAlchemy engine to connect to the database
engine = create_engine(sync_conn_str)

# %%
# df info for baseline table
table_name = "johnwick_baseline_documents"
df = pd.read_sql_table(table_name, engine)
df.info()

# %%
df.head()

# %%



