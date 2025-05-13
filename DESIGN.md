# AIM AIE 6 Certification Challenge: AI-Driven Blog Chat Component

## Task 1: Defining your Problem and Audience

### Problem Statement
Content-rich blogs are difficult for readers to navigate and extract specific information from, leading to poor information retention and reader engagement.


### Target Audience Analysis

For our first implementation, we will focus on content from [TheDataGuy](https://thedataguy.pro) blog, which caters to a technical audience primarily consisting of:

1. **AI/ML Engineers & Researchers** - Professionals working on LLM applications and RAG systems who need guidance on evaluation frameworks and best practices.

2. **Data Scientists & Engineers** - Individuals looking to implement robust data strategies and evaluation methodologies for AI systems.

3. **Technical Leaders & Architects** - Decision-makers seeking insights on AI implementation, data strategy, and technical approaches for enterprise solutions.

4. **Developers Building AI Applications** - Software engineers implementing AI/ML capabilities who need practical advice on topics like RAG systems, evaluation metrics, and feedback loops.

5. **Data Strategists** - Professionals focused on leveraging data as a strategic asset for business success.


### Potential User Questions
1. What is Ragas and how does it help evaluate LLM applications?
2. How do I set up a basic evaluation workflow with Ragas?
3. What are the key metrics to evaluate RAG systems?
4. How can I generate synthetic test data for evaluating my RAG system?
5. How do I create custom metrics in Ragas for my specific use case?
6. What's the difference between Faithfulness and Factual Correctness metrics?
7. How can I build a research agent with RSS feed support like the one described in your blog?
8. What technologies did you use to build your research agent?
9. How can I implement feedback loops to continuously improve my LLM application?
10. Why do you consider data strategy so important for business success?

These questions align with the main themes in the blog posts, which cover LLM evaluation, RAG systems, custom development of AI tools, and data strategy.


## Task 2: Proposed Solution

We propose an AI-driven chat assistant for [TheDataGuy](https://thedataguy.pro)'s blog that enables readers to interactively explore technical content. This component will:

- Provide contextually relevant responses about RAG systems, evaluation metrics, and data strategy
- Allow users to ask clarifying questions about complex concepts without searching across multiple articles
- Deliver code examples and detailed explanations tailored to the user's technical background
- Function as a knowledge companion that has internalized the blog's expertise
- Create a personalized learning experience that adapts to each visitor's specific interests

The solution transforms passive reading into an interactive dialogue, significantly enhancing information discovery and retention.

## Technology Stack

1. **LLM Architecture**: 
    - **Primary Model**: OpenAI `gpt-4.1` - Handles complex tasks including synthetic data generation, sophisticated evaluation workflows, and fine-tuning questions development
    - **Inference Model**: OpenAI `gpt-4o-mini` - Powers the user-facing chat application, offering an optimal balance between performance and cost-efficiency for real-time responses

2. **Embedding Model**: 
    - **Base Model**: `Snowflake/snowflake-arctic-embed-l` - Provides foundation embedding capabilities optimized for technical content with robust semantic understanding
    - **Fine-tuned Model**: `mafzaal/thedataguy_arctic_ft` - Custom-tuned embedding model using query-context pairs extracted from blog content, enhancing retrieval accuracy for domain-specific AI terminology and concepts

3. **Orchestration**: LangChain - Provides flexible components for building LLM applications with robust RAG pipelines and context management tailored for technical blog content.

4. **Vector Database**: Qdrant - Stores embeddings generated through a `pipeline.py` script which also functions as a GitHub workflow to automatically incorporate new blog posts. Provides robust filtering capabilities for content categorization and delivers high performance with manageable operational complexity.

5. **Monitoring**: LangSmith - Integrates seamlessly with LangChain while providing comprehensive tracing, debugging, and performance monitoring specific to LLM applications.

6. **Evaluation**: Ragas - Aligns perfectly with [TheDataGuy](https://thedataguy.pro)'s expertise and blog content, enabling evaluation of the chat system on metrics like faithfulness and relevance. See following notebooks 
    - [05_SDG_Eval](/py-src/notebooks/05_SDG_Eval.ipynb)
    - [07_Fine_Tuning_Dataset](/py-src/notebooks/07_Fine_Tuning_Dataset.ipynb)
    - [07_Fine_Tune_Embeddings](/py-src/notebooks/07_Fine_Tune_Embeddings.ipynb)
    - [07_Fine_Tune_Eval](/py-src/notebooks/07_Fine_Tune_Eval.ipynb)
    
7. **User Interface**: 
    - **Current Implementation**: Chainlit - Provides rapid prototyping capabilities with built-in chat UI components
    - **Production Version**: Custom Svelte component - Delivers a lightweight, responsive interface that seamlessly integrates with the blog's existing design language while minimizing impact on page load performance

## Serving & Inference
- **Development Environment**: Prototype deployed on Hugging Face Spaces for rapid testing and validation, visit [Let's Talk](https://huggingface.co/spaces/mafzaal/lets_talk)
### Future
- **Production Infrastructure**: Azure Container Apps - Provides event-driven autoscaling and enterprise-grade security while integrating with [TheDataGuy](https://thedataguy.pro)'s existing Azure-based technical ecosystem
- **API Layer**: FastAPI - Delivers high-performance endpoints with automatic OpenAPI documentation, facilitating seamless integration with the blog's frontend
- **Deployment Strategy**: CI/CD pipeline using GitHub Actions - Ensures consistent testing and deployment with automated content indexing whenever new blog posts are published

## Agentic Reasoning

Agentic reasoing will be added in future version.


# Task 3: Dealing with the Data

## Data Collection

The blog data from [TheDataGuy](https://thedataguy.pro) was collected and processed for our AI-driven chat component. Below is a summary of the collected blog posts:

| Title | Date | Text Length | URL |
|-------|------|-------------|-----|
| "Coming Back to AI Roots - My Professional Journey" | 2025-04-14 | 5,827 | [Link](https://thedataguy.pro/blog/coming-back-to-ai-roots/) |
| "Data is King: Why Your Data Strategy IS Your Business Strategy" | 2025-04-15 | 6,197 | [Link](https://thedataguy.pro/blog/data-is-king/) |
| "A C# Programmer's Perspective on LangChain Expression Language" | 2025-04-16 | 3,361 | [Link](https://thedataguy.pro/blog/langchain-experience-csharp-perspective/) |
| "Building a Research Agent with RSS Feed Support" | 2025-04-20 | 7,320 | [Link](https://thedataguy.pro/blog/building-research-agent/) |
| "Part 1: Introduction to Ragas: The Essential Evaluation Framework for LLM Applications" | 2025-04-26 | 6,999 | [Link](https://thedataguy.pro/blog/introduction-to-ragas/) |
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

For our blog chat component, we evaluated multiple chunking approaches to optimize retrieval performance:

1. **Initial Experimental Approach**: 
    - Used RecursiveCharacterTextSplitter with chunk size of 1000 characters and 200 character overlap
    - This approach provided granular context chunks for both baseline testing and embedding fine-tuning

2. **Final Implementation Decision**:
    - Opted to use whole blog posts as individual chunks rather than smaller text segments
    - This approach ensures complete retention of article context and coherence
    - Each blog post is treated as a distinct retrievable unit in the vector database

The whole-document chunking strategy was selected to retrieve relevant full blog posts for response generation. This approach preserves article narrative integrity while providing sufficient context for accurate responses.

## Data Statistics Summary

| Statistic | Value |
|-----------|-------|
| Total Blog Posts | 14 |
| Total Characters | 106,275 |
| Minimum Post Length | 1,900 characters |
| Maximum Post Length | 13,468 characters |
| Average Post Length | 7,591 characters |

With average post length under 8,000 characters, whole-document retrieval remains efficient while eliminating contextual fragmentation that occurs with smaller chunks. This approach optimizes for content coherence over granularity, supporting comprehensive responses to technical queries about RAG systems, evaluation frameworks, and data strategy.


## Tools and APIs
We will also using [RSS Feed](https://thedataguy.pro/rss.xml) with tool call to get latest posts which are not yet vectorized


# Task 4: Building a Quick End-to-End Prototype

Live demo at [Let's Talk](https://huggingface.co/spaces/mafzaal/lets_talk) 


# Task 5: Creating a Golden Test Data Set

Synthetic data is available at [Testset](/evals/testset_2.csv), [Eval set](/evals/rag_eval_2.csv) and [Results](/evals/rag_eval_result_2.csv) and here is summary

## Evaluation Results Summary

| Metric | Score |
|--------|-------|
| Faithfulness | 0.8545 |
| Answer Relevancy | 0.3892 |
| Factual Correctness (F1) | 0.2490 |
| Noise Sensitivity (Relevant) | 0.2540 |
| Context Recall | 0.1905 |
| Context Entity Recall | 0.1503 |

These results indicate strong faithfulness but opportunities for improvement in contextual relevance and factual accuracy. The relatively low context recall and entity recall scores suggest that the retrieval component may need refinement to better surface relevant information from the blog content.

# Task 6: Fine-Tuning Open-Source Embeddings

Fine tuning dataset is available at [Link](/evals/ft_questions.csv) and also uploaded at [thedataguy_embed_ft](https://huggingface.co/datasets/mafzaal/thedataguy_embed_ft) and notebook is available at [07_Fine_Tune_Embeddings](/py-src/notebooks/07_Fine_Tune_Embeddings.ipynb)


# Task 7: Assessing Performance

Following is evalation based on finetuned embedding model.

## Fine-Tuned Embedding Model Evaluation Results

| Metric | Score |
|--------|-------|
| Faithfulness | 0.4432 |
| Answer Relevancy | 0.6849 |
| Factual Correctness (F1) | 0.2000 |
| Noise Sensitivity (Relevant) | 0.2033 |
| Context Recall | 0.2500 |
| Context Entity Recall | 0.2175 |

The fine-tuned embedding model shows improved answer relevancy and context recall compared to the base model. While faithfulness decreased, the system demonstrates better ability to retrieve relevant information. These results suggest that the fine-tuning process has shifted the model's strengths toward delivering more contextually appropriate responses, though further optimization is needed to improve faithfulness and factual accuracy.

