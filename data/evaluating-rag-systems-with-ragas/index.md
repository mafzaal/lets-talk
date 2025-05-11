---
title: "Part 3: Evaluating RAG Systems with Ragas"
date: 2025-04-26T20:00:00-06:00
layout: blog
description: "Learn specialized techniques for comprehensive evaluation of Retrieval-Augmented Generation systems using Ragas, including metrics for retrieval quality, generation quality, and end-to-end performance."
categories: ["AI", "RAG", "Evaluation", "Ragas"]
coverImage: "https://images.unsplash.com/photo-1743796055664-3473eedab36e?q=80&w=1974&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
readingTime: 14
published: true
---

In our previous post, we covered the fundamentals of setting up evaluation workflows with Ragas. Now, let's focus specifically on evaluating Retrieval-Augmented Generation (RAG) systems, which present unique evaluation challenges due to their multi-component nature.

## Understanding RAG Systems: More Than the Sum of Their Parts

RAG systems combine two critical capabilities:
1. **Retrieval**: Finding relevant information from a knowledge base
2. **Generation**: Creating coherent, accurate responses based on retrieved information

This dual nature means evaluation must address both components while also assessing their interaction. A system might retrieve perfect information but generate poor responses, or generate excellent prose from irrelevant retrieved content.

## The RAG Evaluation Triad

Effective RAG evaluation requires examining three key dimensions:

1. **Retrieval Quality**: How well does the system find relevant information?
2. **Generation Quality**: How well does the system produce responses from retrieved information?
3. **End-to-End Performance**: How well does the complete system satisfy user needs?

Let's explore how Ragas helps evaluate each dimension of RAG systems.

## Core RAG Metrics in Ragas

Ragas provides specialized metrics to assess RAG systems across retrieval, generation, and end-to-end performance.

### Retrieval Quality Metrics

#### 1. Context Relevancy

Measures how relevant the retrieved documents are to the user's question.

- **How it works:**  
    - Takes the user's question (`user_input`) and the retrieved documents (`retrieved_contexts`).
    - Uses an LLM to score relevance with two different prompts, averaging the results for robustness.
    - Scores are normalized between 0.0 (irrelevant) and 1.0 (fully relevant).

- **Why it matters:**  
    Low scores indicate your retriever is pulling in unrelated or noisy documents. Monitoring this helps you improve the retrieval step.

#### 2. Context Precision

Assesses how much of the retrieved context is actually useful for generating the answer.

- **How it works:**  
    - For each retrieved chunk, an LLM judges if it was necessary for the answer, using the ground truth (`reference`) or the generated response.
    - Calculates [Average Precision](https://en.wikipedia.org/wiki/Evaluation_measures_(information_retrieval)#Average_precision), rewarding systems that rank useful chunks higher.

- **Variants:**  
    - `ContextUtilization`: Uses the generated response instead of ground truth.
    - Non-LLM version: Compares retrieved chunks to ideal reference contexts using string similarity.

- **Why it matters:**  
    High precision means your retriever is efficient; low precision means too much irrelevant information is included.

#### 3. Context Recall

Evaluates whether all necessary information from the ground truth answer is present in the retrieved context.

- **How it works:**  
    - Breaks down the reference answer into sentences.
    - For each sentence, an LLM checks if it can be supported by the retrieved context.
    - The score is the proportion of reference sentences attributed to the retrieved context.

- **Variants:**  
    - Non-LLM version: Compares reference and retrieved contexts using similarity and thresholds.

- **Why it matters:**  
    High recall means your retriever finds all needed information; low recall means critical information is missing.

**Summary:**  
- **Low context relevancy:** Retriever needs better query understanding or semantic matching.
- **Low context precision:** Retriever includes unnecessary information.
- **Low context recall:** Retriever misses critical information.

### Generation Quality Metrics

#### 1. Faithfulness

Checks if the generated answer is factually consistent with the retrieved context, addressing hallucination.

- **How it works:**  
    - Breaks the answer into simple statements.
    - For each, an LLM checks if it can be inferred from the retrieved context.
    - The score is the proportion of faithful statements.

- **Alternative:**  
    - `FaithfulnesswithHHEM`: Uses a specialized NLI model for verification.

- **Why it matters:**  
    High faithfulness means answers are grounded in context; low faithfulness signals hallucination.

#### 2. Answer Relevancy

Measures if the generated answer directly addresses the user's question.

- **How it works:**  
    - Asks an LLM to generate possible questions for the answer.
    - Compares these to the original question using embedding similarity.
    - Penalizes noncommittal answers.

- **Why it matters:**  
    High relevancy means answers are on-topic; low relevancy means answers are off-topic or incomplete.

**Summary:**  
- **Low faithfulness:** Generator adds facts not supported by context.
- **Low answer relevancy:** Generator doesn't focus on the specific question.

### End-to-End Metrics

#### 1. Correctness

Assesses factual alignment between the generated answer and a ground truth reference.

- **How it works:**  
    - Breaks both the answer and reference into claims.
    - Uses NLI to verify claims in both directions.
    - Calculates precision, recall, or F1-score.

- **Why it matters:**  
    High correctness means answers match the ground truth; low correctness signals factual errors.

**Key distinction:**  
- `Faithfulness`: Compares answer to retrieved context.
- `FactualCorrectness`: Compares answer to ground truth.

---

## Common RAG Evaluation Patterns

### 1. High Retrieval, Low Generation Scores

- **Diagnosis:** Good retrieval, poor use of information.
- **Fixes:** Improve prompts, use better generation models, or verify responses post-generation.

### 2. Low Retrieval, High Generation Scores

- **Diagnosis:** Good generation, inadequate information.
- **Fixes:** Enhance indexing, retrieval algorithms, or expand the knowledge base.

### 3. Low Context Precision, High Faithfulness

- **Diagnosis:** Retrieves too much, but generates reliably.
- **Fixes:** Filter passages, optimize chunk size, or use re-ranking.

---

## Best Practices for RAG Evaluation

1. **Evaluate components independently:** Assess retrieval and generation separately.
2. **Use diverse queries:** Include factoid, explanatory, and complex questions.
3. **Compare against baselines:** Test against simpler systems.
4. **Perform ablation studies:** Try variations like different chunk sizes or retrieval models.
5. **Combine with human evaluation:** Use Ragas with human judgment for a complete view.

---

## Conclusion: The Iterative RAG Evaluation Cycle

Effective RAG development is iterative:

1. **Evaluate:** Measure performance.
2. **Analyze:** Identify weaknesses.
3. **Improve:** Apply targeted enhancements.
4. **Re-evaluate:** Measure the impact of changes.

<p align="center">
    <img src="/images/the-iterative-rag-evaluation-cycle.png" alt="The Iterative RAG Evaluation Cycle" width="50%">
</p>

By using Ragas to implement this cycle, you can systematically improve your RAG system's performance across all dimensions.

In our next post, we'll explore how to generate high-quality test datasets for comprehensive RAG evaluation, addressing the common challenge of limited test data.

---

**[Part 1: Introduction to Ragas: The Essential Evaluation Framework for LLM Applications](/blog/introduction-to-ragas/)**  
**[Part 2: Basic Evaluation Workflow](/blog/basic-evaluation-workflow-with-ragas/)**  
**Part 3: Evaluating RAG Systems with Ragas — _You are here_**   
*Next up in the series:*  
**[Part 4: Test Data Generation](/blog/generating-test-data-with-ragas/)**  
**[Part 5: Advanced Evaluation Techniques](/blog/advanced-metrics-and-customization-with-ragas)**  
**[Part 6: Evaluating AI Agents](/blog/evaluating-ai-agents-with-ragas/)**  
**[Part 7: Integrations and Observability](/blog/integrations-and-observability-with-ragas/)**  
**[Part 8: Building Feedback Loops](/blog/building-feedback-loops-with-ragas/)**  


*How have you implemented feedback loops in your LLM applications? What improvement strategies have been most effective for your use cases? If you’re facing specific evaluation hurdles, don’t hesitate to [reach out](https://www.linkedin.com/in/muhammadafzaal/)—we’d love to help!*