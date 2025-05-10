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

# AI-Driven Chat for [TheDataGuy](https://thedataguy.pro): Solution Design

## Proposed Solution

We propose an AI-driven chat assistant for [TheDataGuy](https://thedataguy.pro)'s blog that enables visitors to have interactive conversations about the technical content. This chat component will understand both the blog's content and the user's intent, providing contextually relevant responses about RAG systems, evaluation metrics, data strategy, and other specialized topics covered in the blog. Users will be able to ask clarifying questions about complex concepts, request code examples, or dive deeper into specific aspects of a post without having to search through multiple articles. The experience will feel like having a conversation with a knowledgeable data professional who has internalized all of [TheDataGuy](https://thedataguy.pro)'s expertise, creating a personalized learning experience that adapts to each visitor's technical background and specific interests.

## Technology Stack

1. **LLM**: OpenAI GPT-4.1/o4-mini - Provides an excellent balance of reasoning capabilities, context length, and cost-effectiveness while maintaining high accuracy for technical topics.

2. **Embedding Model**: Huggingface's snowflake-arctic-embed-l - to start with and fine-tuned based to production use.

3. **Orchestration**: LangChain - Provides flexible components for building LLM applications with robust RAG pipelines and context management tailored for technical blog content.

4. **Vector Database**: Qdrant - Self-hostable, offers filtering capabilities ideal for blog content categorization, and provides high performance with reasonable operational complexity.

5. **Monitoring**: LangSmith - Integrates seamlessly with LangChain while providing comprehensive tracing, debugging, and performance monitoring specific to LLM applications.

6. **Evaluation**: Ragas - Aligns perfectly with [TheDataGuy](https://thedataguy.pro)'s expertise and blog content, enabling evaluation of the chat system on metrics like faithfulness and relevance.

7. **User Interface**: Custom Svelte component - Matches the existing blog's aesthetics and provides a lightweight, responsive chat interface with minimal impact on page load times.

8. **Serving & Inference**: Azure Container Apps - Offers scalability and seamless deployment for the chat service while aligning with [TheDataGuy](https://thedataguy.pro)'s technical environment as indicated by the Azure development focus.

## Agentic Reasoning

The solution will implement agentic reasoning in two key areas. First, a research agent will dynamically determine when additional context is needed beyond what's in the vector database, intelligently pulling supplementary information from recent blog posts or external technical documentation when appropriate. Second, a reasoning agent will manage complex technical questions that require multi-step thinking, breaking down queries about implementation details, evaluation methodologies, or architectural decisions into logical components before synthesizing comprehensive answers. This approach will be particularly valuable when users ask about applying concepts across multiple blog posts (e.g., "How would I evaluate a research agent using Ragas?") where simple retrieval wouldn't provide a satisfactory response.


# Task 3: Dealing with the Data

We will be using data source

1. Markdown blog post files from [TheDataGuy](https://thedataguy.pro)' from github at [mafzaal](https://github.com/mafzaal/mafzaal.github.io)
2. Python code files from [TheDataGuy](https://thedataguy.pro)'s from github at [intro-to-ragas](https://github.com/mafzaal/intro-to-ragas) and [AIE6-ResearchAgent](https://github.com/mafzaal/AIE6-ResearchAgent)