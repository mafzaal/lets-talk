# AIM AIE 6 Certification Challenge: AI-Driven Blog Chat Component

## Task 1: Defining the Problem and Audience

### Problem Statement
Content-rich technical blogs are difficult to navigate, making information extraction challenging and resulting in reduced reader engagement and information retention.

### Target Audience Analysis

Our initial implementation focuses on [TheDataGuy](https://thedataguy.pro) blog, which serves a technical audience including:

1. **AI/ML Engineers & Researchers** - Professionals seeking guidance on LLM applications, RAG systems, and evaluation frameworks
   
2. **Data Scientists & Engineers** - Practitioners implementing data strategies and evaluation methodologies for AI systems
   
3. **Technical Leaders & Architects** - Decision-makers exploring AI implementation, data strategy, and enterprise solutions
   
4. **Developers Building AI Applications** - Engineers needing practical advice on RAG systems and evaluation metrics
   
5. **Data Strategists** - Professionals leveraging data as a strategic business asset


### Potential User Questions
1. What is Ragas and how does it help evaluate LLM applications?
2. How do I set up a basic evaluation workflow with Ragas?
3. What are the key metrics to evaluate RAG systems?
4. How can I generate synthetic test data for my RAG system?
5. How do I create custom metrics in Ragas for specific use cases?
6. What's the difference between Faithfulness and Factual Correctness metrics?
7. How can I build a research agent with RSS feed support?
8. What technologies are optimal for building a research agent?
9. How can I implement feedback loops to improve my LLM application?
10. Why is data strategy critical for business success?

These questions align with the blog's main themes: LLM evaluation, RAG systems, AI tool development, and data strategy.


## Task 2: Proposed Solution

We propose an AI-driven chat assistant for [TheDataGuy](https://thedataguy.pro)'s blog that enables readers to interactively explore technical content. This solution will:

- Provide contextually relevant responses on RAG systems, evaluation metrics, and data strategy
- Enable users to ask clarifying questions without searching across multiple articles
- Deliver code examples and explanations tailored to users' technical backgrounds
- Function as a knowledge companion with the blog's expertise
- Create personalized learning experiences based on visitors' specific interests

This solution transforms passive reading into interactive dialogue, enhancing information discovery and retention.

## Technology Stack

1. **LLM Architecture**: 
   - **Primary Model**: OpenAI `gpt-4.1` - For complex tasks including synthetic data generation and evaluation workflows
   - **Inference Model**: OpenAI `gpt-4o-mini` - Powers the chat application with optimal performance/cost balance

2. **Embedding Model**: 
   - **Base Model**: `Snowflake/snowflake-arctic-embed-l` - Foundation embedding capabilities for technical content
   - **Fine-tuned Model**: `mafzaal/thedataguy_arctic_ft` - Custom-tuned using blog-specific query-context pairs

3. **Orchestration**: LangChain - Flexible components for LLM applications with robust RAG pipelines and context management

4. **Vector Database**: Qdrant - Stores embeddings via `pipeline.py` with GitHub workflow automation for new blog posts

5. **Monitoring**: LangSmith - Seamless LangChain integration with comprehensive tracing and performance monitoring

6. **Evaluation**: Ragas - Perfect alignment with [TheDataGuy](https://thedataguy.pro)'s expertise for metrics like faithfulness and relevance:
   - [05_SDG_Eval](/py-src/notebooks/05_SDG_Eval.ipynb)
   - [07_Fine_Tuning_Dataset](/py-src/notebooks/07_Fine_Tuning_Dataset.ipynb)
   - [07_Fine_Tune_Embeddings](/py-src/notebooks/07_Fine_Tune_Embeddings.ipynb)
   - [07_Fine_Tune_Eval](/py-src/notebooks/07_Fine_Tune_Eval.ipynb)
    
7. **User Interface**: 
   - **Current**: Chainlit - Rapid prototyping with built-in chat UI components
   - **Production**: Custom Svelte component - Lightweight, responsive interface integrating with the blog's design

## Serving & Inference
- **Development**: Prototype on Hugging Face Spaces ([Let's Talk](https://huggingface.co/spaces/mafzaal/lets_talk))
### Future
- **Production**: Azure Container Apps - Event-driven autoscaling with enterprise-grade security
- **API Layer**: FastAPI - High-performance endpoints with automatic OpenAPI documentation
- **Deployment**: CI/CD via GitHub Actions - Consistent testing with automated content indexing for new blog posts

## Agentic Reasoning

Agentic reasoning will be added in a future version.


# Task 3: Dealing with the Data

## Data Collection

The blog data from [TheDataGuy](https://thedataguy.pro) was collected and processed for our chat component. Summary of collected posts:

| Title | Date | Length | URL |
|-------|------|--------|-----|
| "Coming Back to AI Roots - My Professional Journey" | 2025-04-14 | 5,827 | [Link](https://thedataguy.pro/blog/coming-back-to-ai-roots/) |
| "Data is King: Why Your Data Strategy IS Your Business Strategy" | 2025-04-15 | 6,197 | [Link](https://thedataguy.pro/blog/data-is-king/) |
| "A C# Programmer's Perspective on LangChain Expression Language" | 2025-04-16 | 3,361 | [Link](https://thedataguy.pro/blog/langchain-experience-csharp-perspective/) |
| "Building a Research Agent with RSS Feed Support" | 2025-04-20 | 7,320 | [Link](https://thedataguy.pro/blog/building-research-agent/) |
| "Part 1: Introduction to Ragas: The Essential Evaluation Framework" | 2025-04-26 | 6,999 | [Link](https://thedataguy.pro/blog/introduction-to-ragas/) |
| "Part 2: Basic Evaluation Workflow with Ragas" | 2025-04-26 | 11,223 | [Link](https://thedataguy.pro/blog/basic-evaluation-workflow-with-ragas/) |
| "Part 3: Evaluating RAG Systems with Ragas" | 2025-04-26 | 8,811 | [Link](https://thedataguy.pro/blog/evaluating-rag-systems-with-ragas/) |
| "Part 4: Generating Test Data with Ragas" | 2025-04-27 | 14,682 | [Link](https://thedataguy.pro/blog/generating-test-data-with-ragas/) |
| "Part 5: Advanced Metrics and Customization with Ragas" | 2025-04-28 | 11,531 | [Link](https://thedataguy.pro/blog/advanced-metrics-and-customization-with-ragas/) |
| "Part 6: Evaluating AI Agents: Beyond Simple Answers with Ragas" | 2025-04-28 | 9,822 | [Link](https://thedataguy.pro/blog/evaluating-ai-agents-with-ragas/) |
| "Part 7: Integrations and Observability with Ragas" | 2025-04-30 | 9,100 | [Link](https://thedataguy.pro/blog/integrations-and-observability-with-ragas/) |
| "Subscribe to Our Blog via RSS" | 2025-05-03 | 2,139 | [Link](https://thedataguy.pro/blog/rss-feed-announcement/) |
| "Part 8: Building Feedback Loops with Ragas" | 2025-05-04 | 8,160 | [Link](https://thedataguy.pro/blog/building-feedback-loops-with-ragas/) |
| "Metric-Driven Development: Make Smarter Decisions, Faster" | 2025-05-05 | 12,450 | [Link](https://thedataguy.pro/blog/metric-driven-development/) |


## Chunking Strategy

For our blog chat component, we evaluated multiple chunking approaches:

1. **Initial Experiment**: 
   - RecursiveCharacterTextSplitter with 1000-character chunks and 200-character overlap
   - Provided granular context chunks for baseline testing and embedding fine-tuning

2. **No Chunking Implementation**:
   - Whole blog posts as individual chunks to preserve complete article context
   - Each post treated as a distinct retrievable unit in the vector database

3. **Final Implementation**:
   - RecursiveCharacterTextSplitter with 1000-character chunks and 200-character overlap
   - `mafzaal/thedataguy_arctic_ft` Fine-tuned model on [TheDataGuy](https://thedataguy.pro/)'s blog posts.


The whole-document strategy preserves article narrative integrity while providing sufficient context for accurate responses.

## Data Statistics Summary

| Statistic | Value |
|-----------|-------|
| Total Blog Posts | 14 |
| Total Characters | 106,275 |
| Minimum Post Length | 1,900 chars |
| Maximum Post Length | 13,468 chars |
| Average Post Length | 7,591 chars |

With average post length under 8,000 characters, whole-document retrieval remains efficient while maintaining content coherence, supporting comprehensive responses about RAG systems, evaluation frameworks, and data strategy.

## Tools and APIs

Our implementation leverages several tools and APIs for data processing and integration:

1. **Content Retrieval**:
   - [RSS Feed](https://thedataguy.pro/rss.xml) - Automated collection of latest blog posts
   - Custom scraping scripts for initial content extraction
   - GitHub Actions for scheduled content updates

2. **Data Processing**:
   - LangChain DocumentLoaders - Structured parsing of blog content
   - DateTime API - Timestamping and content freshness verification

3. **Integration**:
   - Tool Calls functionality - Enables dynamic content updates from RSS
   - LangSmith API - Monitoring and tracking system performance

This toolset enables automated content discovery, processing, and integration into our vector database, ensuring the chat component stays current with the latest blog posts.

# Task 4: Building a Quick End-to-End Prototype

Live demo available at [Let's Talk](https://huggingface.co/spaces/mafzaal/lets_talk) 


# Task 5: Creating a Golden Test Data Set

Synthetic data available at [Testset](/evals/testset_2.csv), [Eval set](/evals/rag_eval_2.csv) and [Results](/evals/rag_eval_result_2.csv).

## Evaluation Results Summary

| Metric | Score |
|--------|-------|
| Faithfulness | 0.8545 |
| Answer Relevancy | 0.3892 |
| Factual Correctness (F1) | 0.2490 |
| Noise Sensitivity (Relevant) | 0.2540 |
| Context Recall | 0.1905 |
| Context Entity Recall | 0.1503 |

These results show strong faithfulness but opportunities for improvement in contextual relevance and factual accuracy. The low context recall and entity recall scores suggest the retrieval component needs refinement to better surface relevant information from blog content.

# Task 6: Fine-Tuning Open-Source Embeddings

Fine-tuning dataset available at [Link](/evals/ft_questions.csv) and uploaded to [thedataguy_embed_ft](https://huggingface.co/datasets/mafzaal/thedataguy_embed_ft). Implementation in [07_Fine_Tune_Embeddings](/py-src/notebooks/07_Fine_Tune_Embeddings.ipynb).

# Task 7: Assessing Performance

Evaluation based on fine-tuned embedding model:

## Fine-Tuned Embedding Model Evaluation Results

| Metric | Score |
|--------|-------|
| Faithfulness | 0.4432 |
| Answer Relevancy | 0.6849 |
| Factual Correctness (F1) | 0.2000 |
| Noise Sensitivity (Relevant) | 0.2033 |
| Context Recall | 0.2500 |
| Context Entity Recall | 0.2175 |

The fine-tuned model shows improved answer relevancy and context recall compared to the base model. While faithfulness decreased, the system better retrieves relevant information. These results suggest the fine-tuning process shifted strengths toward contextually appropriate responses, though further optimization is needed for faithfulness and factual accuracy.

