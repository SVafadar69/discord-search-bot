

from dotenv import load_dotenv 
import os 
import openai 
import discord
from typing import List
from chromadb.utils import embedding_functions
from chromadb.utils.embedding_functions import ChromaCloudSpladeEmbeddingFunction
from chromadb.execution.expression.operator import K
from chromadb import Search, K, Knn, Rrf, Schema, SparseVectorIndexConfig, K
load_dotenv()


openai_api_key = os.getenv("openai_api_key")
chromadb_api_key = os.getenv("chromadb_api_key")
chromadb_tenant= os.getenv("chromadb_tenant")
chromadb_database= os.getenv("chromadb_database")
chroma_collection_name = os.getenv("CHROMA_COLLECTION_NAME")
discord_bot_token = os.getenv("discord_bot_token")
discord_channel_id = int(os.getenv("discord_channel_id"))

CHUNK_SIZE = 3

client = discord.Client(intents=discord.Intents.default())

schema = Schema()


sparse_ef = ChromaCloudSpladeEmbeddingFunction()
schema.create_index(
    config=SparseVectorIndexConfig(
        source_key=K.DOCUMENT,
        embedding_function=sparse_ef
    ),
    key="sparse_embedding"
)

collection_anduril = client.get_or_create_collection(
    name=chroma_collection_name,
    schema=schema
)

def run_hybrid_search(collection, query, limit=30):
    """Combined semantic and keyword search using RRF."""
    ranker = Rrf(
        ranks=[
            Knn(query=query, return_rank=True),
            Knn(query=query, key="sparse_embedding", return_rank=True)
        ],
        weights=[0.5, 0.5],
        k=100
    )
    search = (Search()
              .rank(ranker)
              .limit(limit)
              .select(K.DOCUMENT, K.SCORE))
    return collection.search(search)

def retrieve_collection(collection_name: str, schema: Schema, client: chromadb.CloudClient): 
    collection = client.get_or_create_collection(name=collection_name,schema=schema)
    return collection

def retrieve_prompt(prompt_name: str) -> str: 
    prompt = open(prompt_name, 'r', encoding='utf-8').read()
    return prompt

def rewrite_query(system_prompt: str) -> str: 
    response = openai_client.responses.create(
        model="gpt-5.4-nano",
        input=system_prompt 
    )
    return response.output_text

def chunk_documents(documents):
    step = CHUNK_SIZE - OVERLAP

    for chunk_start in range(0, len(documents), step):
        chunk = formatted_messages_shay[chunk_start:chunk_start + CHUNK_SIZE]

        if not chunk:
            continue

        chunk_end = chunk_start + len(chunk) - 1

        ids = [
            f"shay_chunk_{chunk_start}_{chunk_end}"
        ]

        documents = [
            "\n".join(
                msg["text"]
                for msg in chunk
            )
        ]

        metadatas = [
            {
                "messages_metadata": json.dumps([
                    {
                        "date": str(msg["date"]),
                        "sender": msg["sender"],
                        "recipient": msg["recipient"],
                    }
                    for msg in chunk
                ])
            }
        ]


        collection_shay_all.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )

        print(f"Uploaded shay chunk {chunk_start} to {chunk_end}")


@client.event
async def on_rate_limit(payload):
    print(f'Rate limit hit -> bucket: {payload.bucket}')

@client.event
async def on_ready():
    channel = client.get_channel(discord_channel_id)
    print(f'channel: {channel}')
    messages = [msg async for msg in channel.history(limit=None)]
    print(messages[-3].content)
    print('\n', type(messages[0]))
    print(messages[1])
    print('\n')
    print(messages[2])
    print('\n', messages[2])

    print(f"Got {len(messages)} messages")
    await client.close()



client.run(discord_bot_token)