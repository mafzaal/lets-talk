---
title: Lets Talk
emoji: 🐨
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
---

# Welcome to TheDataGuy Chat! 👋

This is a Q&A chatbot powered by TheDataGuy blog posts. Ask questions about topics covered in the blog, such as:

- RAGAS and RAG evaluation
- Building research agents
- Metric-driven development
- Data science best practices

## How it works

Under the hood, this application uses:

1. **Snowflake Arctic Embeddings**: To convert text into vector representations
2. **Qdrant Vector Database**: To store and search for similar content
3. **GPT-4o-mini**: To generate helpful responses based on retrieved content
4. **LangChain**: For building the RAG workflow
5. **Chainlit**: For the chat interface

## Sources

All answers are generated based on content from [TheDataGuy blog](https://thedataguy.pro/blog/). Sources are shown for each response so you can read more about the topic.


```bash
docker build -t lets-talk .
docker run -p 7860:7860 \
    --env-file ./.env \
    lets-talk
```

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference
