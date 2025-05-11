---
title: "Part 4: Generating Test Data with Ragas"
date: 2025-04-27T16:00:00-06:00
layout: blog
description: "Discover how to generate robust test datasets for evaluating Retrieval-Augmented Generation systems using Ragas, including document-based, domain-specific, and adversarial test generation techniques."
categories: ["AI", "RAG", "Evaluation", "Ragas","Data"]
coverImage: "/images/generating_test_data.png"
readingTime: 14
published: true
---


In our previous post, we explored how to comprehensively evaluate RAG systems using specialized metrics. However, even the best evaluation framework requires high-quality test data to yield meaningful insights. In this post, we'll dive into how Ragas helps you generate robust test datasets for evaluating your LLM applications.


## Why and How to Generate Synthetic Data for RAG Evaluation

In the world of Retrieval-Augmented Generation (RAG) and LLM-powered applications, **synthetic data generation** is a game-changer for rapid iteration and robust evaluation. This blog post explains why synthetic data is essential, and how you can generate it for your own RAG pipelines—using modern tools like [RAGAS](https://github.com/explodinggradients/ragas) and [LangSmith](https://smith.langchain.com/).

---

### Why Generate Synthetic Data?

1. **Early Signal, Fast Iteration**  
   Real-world data is often scarce or expensive to label. Synthetic data lets you quickly create test sets that mimic real user queries and contexts, so you can evaluate your system’s performance before deploying to production.

2. **Controlled Complexity**  
   You can design synthetic datasets to cover edge cases, multi-hop reasoning, or specific knowledge domains—ensuring your RAG system is robust, not just good at the “easy” cases.

3. **Benchmarking and Comparison**  
   Synthetic test sets provide a repeatable, comparable way to measure improvements as you tweak your pipeline (e.g., changing chunk size, embeddings, or prompts).

---

### How to Generate Synthetic Data

#### 1. **Prepare Your Source Data**
Start with a set of documents relevant to your domain. For example, you might download and load HTML blog posts into a document format using tools like LangChain’s `DirectoryLoader`.

#### 2. **Build a Knowledge Graph**
Use RAGAS to convert your documents into a knowledge graph. This graph captures entities, relationships, and summaries, forming the backbone for generating meaningful queries. RAGAS applies default transformations are dependent on the corpus length, here are some examples:

- Producing Summaries -> produces summaries of the documents
- Extracting Headlines -> finding the overall headline for the document
- Theme Extractor -> extracts broad themes about the documents

It then uses cosine-similarity and heuristics between the embeddings of the above transformations to construct relationships between the nodes. This is a crucial step, as the quality of your knowledge graph directly impacts the relevance and accuracy of the generated queries.

#### 3. **Configure Query Synthesizers**
RAGAS provides several query synthesizers:
- **SingleHopSpecificQuerySynthesizer**: Generates direct, fact-based questions.
- **MultiHopAbstractQuerySynthesizer**: Creates broader, multi-step reasoning questions.
- **MultiHopSpecificQuerySynthesizer**: Focuses on questions that require connecting specific entities across documents.

By mixing these, you get a diverse and challenging test set.

#### 4. **Generate the Test Set**
With your knowledge graph and query synthesizers, use RAGAS’s `TestsetGenerator` to create a synthetic dataset. This dataset will include questions, reference answers, and supporting contexts.

#### 5. **Evaluate and Iterate**
Load your synthetic dataset into an evaluation platform like LangSmith. Run your RAG pipeline against the test set, and use automated evaluators (for accuracy, helpfulness, style, etc.) to identify strengths and weaknesses. Tweak your pipeline and re-evaluate to drive improvements.

---

### Minimal Example

Here’s a high-level pseudocode outline (see the notebook for full details):

````python
# 1. Load documents
from langchain_community.document_loaders import DirectoryLoader
path = "data/"
loader = DirectoryLoader(path, glob="*.md")
docs = loader.load()

# 2. Generate data
from ragas.testset import TestsetGenerator
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
# Initialize the generator with the LLM and embedding model
generator_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4.1"))
generator_embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings())

# Create the test set generator
generator = TestsetGenerator(llm=generator_llm, embedding_model=generator_embeddings)
dataset = generator.generate_with_langchain_docs(docs, testset_size=10)
````

`dataset` will now contain a set of questions, answers, and contexts that you can use to evaluate your RAG system.

> 💡 **Try it yourself:**  
> Explore the hands-on notebook for synthetic data generation:  
> 💡 **Try it yourself:**  
> Explore the hands-on notebook for synthetic data generation:  
> [04_Synthetic_Data_Generation](https://github.com/mafzaal/intro-to-ragas/blob/master/04_Synthetic_Data_Generation.ipynb)

### Understanding the Generated Dataset Columns

The synthetic dataset generated by Ragas typically includes the following columns:

- **`user_input`**: The generated question or query that simulates what a real user might ask. This is the prompt your RAG system will attempt to answer.
- **`reference_contexts`**: A list of document snippets or passages that contain the information needed to answer the `user_input`. These serve as the ground truth retrieval targets.
- **`reference`**: The ideal answer to the `user_input`, based strictly on the `reference_contexts`. This is used as the gold standard for evaluating answer accuracy.
- **`synthesizer_name`**: The name of the query synthesizer (e.g., `SingleHopSpecificQuerySynthesizer`, `MultiHopAbstractQuerySynthesizer`) that generated the question. This helps track the type and complexity of each test case.

These columns enable comprehensive evaluation by linking each question to its supporting evidence and expected answer, while also providing insight into the diversity and difficulty of the generated queries.


## Deep Dive into Test Data Generation

So you have a collection of documents and want to create a robust evaluation dataset for your RAG system using Ragas. The `TestsetGenerator`'s `generate_with_langchain_docs` method is your starting point. But what exactly happens when you call it? Let's peek under the hood.

**The Goal:** To take raw Langchain `Document` objects and transform them into a structured Ragas `Testset` containing diverse question-answer pairs grounded in those documents.

**The Workflow:**

1.  **Input & Validation:** The function receives your Langchain `documents`, the desired `testset_size`, and optional configurations for transformations and query types. It first checks if it has the necessary LLM and embedding models to proceed (either provided during `TestsetGenerator` initialization or passed directly to this method).

2.  **Setting Up Transformations:** This is a crucial step.
    *   **User-Provided:** If you pass a specific `transforms` configuration, the generator uses that.
    *   **Default Transformations:** If you *don't* provide `transforms`, the generator calls `ragas.testset.transforms.default_transforms`. This sets up a standard pipeline to process your raw documents into a usable knowledge graph foundation. We'll detail this below.

3.  **Document Conversion:** Your Langchain `Document` objects are converted into Ragas' internal `Node` representation, specifically `NodeType.DOCUMENT`. Each node holds the `page_content` and `metadata`.

4.  **Initial Knowledge Graph:** A `KnowledgeGraph` object is created, initially containing just these document nodes.

5.  **Applying Transformations:** The core processing happens here using `ragas.testset.transforms.apply_transforms`. The chosen `transforms` (default or custom) are executed sequentially on the `KnowledgeGraph`. This modifies the graph by:
    *   Adding new nodes (e.g., chunks, questions, answers).
    *   Adding relationships between nodes (e.g., linking a question to the chunk it came from).
    The generator's internal `knowledge_graph` attribute is updated with this processed graph.

6.  **Delegation to `generate()`:** Now that the foundational knowledge graph with basic Q&A pairs is built (thanks to transformations), `generate_with_langchain_docs` calls the main `self.generate()` method. This method handles the final step of creating the diverse test samples.

**Spotlight: Default Transformations (`default_transforms`)**

When you don't specify custom transformations, Ragas applies a sensible default pipeline to prepare your documents:

1.  **Chunking (`SentenceChunker`):** Breaks down your large documents into smaller, more manageable chunks (often sentences or groups of sentences). This is essential for focused retrieval and question generation.
2.  **Embedding:** Generates vector embeddings for each chunk using the provided embedding model. These are needed for similarity-based operations.
3.  **Filtering (`SimilarityFilter`, `InformationFilter`):** Removes redundant chunks (those too similar to others) and potentially low-information chunks to clean up the knowledge base.
4.  **Base Q&A Generation (`QAGenerator`):** This is where the initial, simple question-answer pairs are created. The generator looks at individual (filtered) chunks and uses an LLM to formulate straightforward questions whose answers are directly present in that chunk.

Essentially, the default transformations build a knowledge graph populated with embedded, filtered document chunks and corresponding simple, extractive question-answer pairs.

**Spotlight: Query Synthesizers (via `self.generate()` and `default_query_distribution`)**

The `self.generate()` method, called by `generate_with_langchain_docs`, is responsible for taking the foundational graph and creating the final, potentially complex, test questions using **Query Synthesizers** (also referred to as "evolutions" or "scenarios").

*   **Query Distribution:** `self.generate()` uses a `query_distribution` parameter. If you don't provide one, it calls `ragas.testset.synthesizers.default_query_distribution`.
*   **Default Synthesizers:** This default distribution defines a mix of different synthesizer types and the probability of using each one. Common defaults include:
    *   **`simple`:** Takes the base Q&A pairs generated during transformation and potentially rephrases them slightly.
    *   **`reasoning`:** Creates questions requiring logical inference based on the context in the graph.
    *   **`multi_context`:** Generates questions needing information synthesized from multiple different chunks/nodes in the graph.
    *   **`conditional`:** Creates questions with "if/then" clauses based on information in the graph.
*   **Generation Process:** `self.generate()` calculates how many questions of each type to create based on the `testset_size` and the distribution probabilities. It then uses an `Executor` to run the appropriate synthesizers, generating the final `TestsetSample` objects that make up your evaluation dataset.

**In Summary:**

`generate_with_langchain_docs` orchestrates a two-phase process:

1.  **Transformation Phase:** Uses (typically default) transformations like chunking, filtering, and base Q&A generation to build a foundational knowledge graph from your documents.
2.  **Synthesis Phase (via `self.generate`):** Uses (typically default) query synthesizers/evolutions (`simple`, `reasoning`, `multi_context`, etc.) to create diverse and complex questions based on the information stored in the transformed knowledge graph.

This automated pipeline allows you to go from raw documents to a rich, multi-faceted evaluation dataset with minimal configuration.


## Best Practices for Test Data Generation

1. **Start small and iterate**: Begin with a small test set to verify quality before scaling up
2. **Diversify document sources**: Include different document types, styles, and domains
3. **Balance question types**: Ensure coverage of simple, complex, and edge-case scenarios
4. **Manual review**: Sample-check generated questions for quality and relevance
5. **Progressive difficulty**: Include both easy and challenging questions to identify performance thresholds
6. **Document metadata**: Retain information about test case generation for later analysis
7. **Version control**: Track test set versions alongside your application versions

## Conclusion: Building a Test Data Generation Strategy

Test data generation should be an integral part of your LLM application development cycle:

1. **Initial development**: Generate broad test sets to identify general capabilities and limitations
2. **Refinement**: Create targeted test sets for specific features or improvements
3. **Regression testing**: Maintain benchmark test sets to ensure changes don't break existing functionality
4. **Continuous improvement**: Generate new test cases as your application evolves

By leveraging Ragas for automated test data generation, you can build comprehensive evaluation datasets that thoroughly exercise your LLM applications, leading to more robust, reliable systems.

In our next post, we'll explore advanced metrics and customization techniques for specialized evaluation needs.

---


**[Part 1: Introduction to Ragas: The Essential Evaluation Framework for LLM Applications](/blog/introduction-to-ragas/)**  
**[Part 2: Basic Evaluation Workflow](/blog/basic-evaluation-workflow-with-ragas/)**  
**[Part 3: Evaluating RAG Systems with Ragas](/blog/evaluating-rag-systems-with-ragas/)**   
**Part 4: Test Data Generation — _You are here_**  
*Next up in the series:*  
**[Part 5: Advanced Evaluation Techniques](/blog/advanced-metrics-and-customization-with-ragas)**  
**[Part 6: Evaluating AI Agents](/blog/evaluating-ai-agents-with-ragas/)**  
**[Part 7: Integrations and Observability](/blog/integrations-and-observability-with-ragas/)**  
**[Part 8: Building Feedback Loops](/blog/building-feedback-loops-with-ragas/)**  


*How have you implemented feedback loops in your LLM applications? What improvement strategies have been most effective for your use cases? If you’re facing specific evaluation hurdles, don’t hesitate to [reach out](https://www.linkedin.com/in/muhammadafzaal/)—we’d love to help!* 