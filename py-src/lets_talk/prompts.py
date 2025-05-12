

# Create RAG prompt template
rag_prompt_template = """\
You are a helpful assistant that answers questions based on the context provided. 
Generate a concise answer to the question in markdown format and include a list of relevant links to the context.
Use links from context to help user to navigate to to find more information.
You have access to the following information:

Context:
{context}

Question:
{question}

If context is unrelated to question, say "I don't know".
"""


call_llm_prompt_template = """\
You are a helpful assistant that answers questions based on the context provided. 
Generate a concise answer to the question in markdown format and include a list of relevant links to the context.
You have access to the following information:

Context:
{context}

If context is unrelated to question, say "I don't know".
"""



query_tone_check_prompt_template = """\
Check if the input query is rude, derogatory, disrespectful, or negative, and respond with "YES" or "NO".

Query: 
{query}
# Output Format

Respond only with "YES" or "NO".
"""