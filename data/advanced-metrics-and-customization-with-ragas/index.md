---
title: "Part 5: Advanced Metrics and Customization with Ragas"
date: 2025-04-28T05:00:00-06:00
layout: blog
description: "Explore advanced metrics and customization techniques in Ragas for evaluating LLM applications, including creating custom metrics, domain-specific evaluation, composite scoring, and best practices for building a comprehensive evaluation ecosystem."
categories: ["AI", "RAG", "Evaluation", "Ragas","Data"]
coverImage: "https://plus.unsplash.com/premium_photo-1661368994107-43200954c524?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
readingTime: 9
published: true
---

In our previous post, we explored how to generate comprehensive test datasets for evaluating LLM applications. Now, let's dive into one of Ragas' most powerful capabilities: advanced metrics and custom evaluation approaches that address specialized evaluation needs.

## Beyond the Basics: Why Advanced Metrics Matter

While Ragas' core metrics cover fundamental evaluation aspects, real-world applications often have unique requirements:

- **Domain-specific quality criteria**: Legal, medical, or financial applications have specialized accuracy requirements
- **Custom interaction patterns**: Applications with unique conversation flows need tailored evaluation approaches
- **Specialized capabilities**: Features like reasoning, code generation, or structured output demand purpose-built metrics
- **Business-specific KPIs**: Aligning evaluation with business objectives requires customized metrics

Let's explore how to extend Ragas' capabilities to meet these specialized needs.

## Understanding Ragas' Metric Architecture

Before creating custom metrics, it's helpful to understand Ragas' metric architecture:

### 1. Understand the Metric Base Classes

All metrics in Ragas inherit from the abstract `Metric` class (see `metrics/base.py`). For most use cases, you’ll extend one of these:

- **SingleTurnMetric**: For metrics that evaluate a single question/response pair.
- **MultiTurnMetric**: For metrics that evaluate multi-turn conversations.
- **MetricWithLLM**: For metrics that require an LLM for evaluation.
- **MetricWithEmbeddings**: For metrics that use embeddings.

You can mix these as needed (e.g., `MetricWithLLM, SingleTurnMetric`).

Each metric implements specific scoring methods depending on its type:

- `_single_turn_ascore`: For single-turn metrics
- `_multi_turn_ascore`: For multi-turn metrics


## Creating Your First Custom Metric

Let's create a custom metric that evaluates technical accuracy in programming explanations:

```python
from dataclasses import dataclass, field
from typing import Dict, Optional, Set
import typing as t

from ragas.metrics.base import MetricWithLLM, SingleTurnMetric
from ragas.prompt import PydanticPrompt
from ragas.metrics import MetricType, MetricOutputType
from pydantic import BaseModel

# Define input/output models for the prompt
class TechnicalAccuracyInput(BaseModel):
    question: str
    context: str
    response: str
    programming_language: str = "python"

class TechnicalAccuracyOutput(BaseModel):
    score: float
    feedback: str


# Define the prompt
class TechnicalAccuracyPrompt(PydanticPrompt[TechnicalAccuracyInput, TechnicalAccuracyOutput]):
    instruction: str = (
        "Evaluate the technical accuracy of the response to a programming question. "
        "Consider syntax correctness, algorithmic accuracy, and best practices."
    )
    input_model = TechnicalAccuracyInput
    output_model = TechnicalAccuracyOutput
    examples = [
        # Add examples here
    ]

# Create the metric
@dataclass
class TechnicalAccuracy(MetricWithLLM, SingleTurnMetric):
    name: str = "technical_accuracy"
    _required_columns: Dict[MetricType, Set[str]] = field(
        default_factory=lambda: {
            MetricType.SINGLE_TURN: {
                "user_input",
                "response",
                
            }
        }
    )
    output_type: Optional[MetricOutputType] = MetricOutputType.CONTINUOUS
    evaluation_prompt: PydanticPrompt = field(default_factory=TechnicalAccuracyPrompt)
    
    async def _single_turn_ascore(self, sample, callbacks) -> float:
        assert self.llm is not None, "LLM must be set"
        
        question = sample.user_input
        response = sample.response
        # Extract programming language from question if possible
        programming_language = "python"  # Default
        languages = ["python", "javascript", "java", "c++", "rust", "go"]
        for lang in languages:
            if lang in question.lower():
                programming_language = lang
                break
        
        # Get the context
        context = "\n".join(sample.retrieved_contexts) if sample.retrieved_contexts else ""
        
        # Prepare input for prompt
        prompt_input = TechnicalAccuracyInput(
            question=question,
            context=context,
            response=response,
            programming_language=programming_language
        )
        
        # Generate evaluation
        evaluation = await self.evaluation_prompt.generate(
            data=prompt_input, llm=self.llm, callbacks=callbacks
        )
        
        return evaluation.score
```
## Using the Custom Metric
To use the custom metric, simply include it in your evaluation pipeline:

```python
from langchain_openai import ChatOpenAI
from ragas import SingleTurnSample
from ragas.llms import LangchainLLMWrapper

# Initialize the LLM, you are going to OPENAI API key
evaluator_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o")) 

test_data = {
    "user_input": "Write a function to calculate the factorial of a number in Python.",
    "retrieved_contexts": ["Python is a programming language.", "A factorial of a number n is the product of all positive integers less than or equal to n."],
    "response": "def factorial(n):\n    if n == 0:\n        return 1\n    else:\n        return n * factorial(n-1)",
}

# Create a sample
sample = SingleTurnSample(**test_data)  # Unpack the dictionary into the constructor
technical_accuracy = TechnicalAccuracy(llm=evaluator_llm)
score = await technical_accuracy.single_turn_ascore(sample)
print(f"Technical Accuracy Score: {score}")
# Note: The above code is a simplified example. In a real-world scenario, you would need to handle exceptions,
```
You can also use the `evaluate` function to evaluate a dataset:

```python
from ragas import evaluate
from ragas import evaluate

results = evaluate(
    dataset, # Your dataset of samples
    metrics=[TechnicalAccuracy(), ...],
    llm=myevaluator_llm_llm
)
```

> 💡 **Try it yourself:**  
> Explore the hands-on notebook for synthetic data generation:  
> [05_Advanced_Metrics_and_Customization](https://github.com/mafzaal/intro-to-ragas/blob/master/05_Advanced_Metrics_and_Customization.ipynb)

## Customizing Metrics for Your Application

You can further refine your evaluation by customizing existing metrics—such as adjusting thresholds or criteria—to better fit your application's requirements. For multi-turn conversations, you might configure metrics like topic adherence to emphasize specific aspects, such as precision or recall, based on your evaluation objectives.

In specialized domains like healthcare or legal, it's crucial to design custom metrics that capture domain-specific accuracy and compliance needs. For complex applications, consider combining several metrics into composite scores to represent multiple quality dimensions.

When assessing capabilities like code generation or structured outputs, develop metrics that evaluate execution correctness or schema compliance. For advanced scenarios, you can build metric pipelines that orchestrate several metrics and aggregate their results using strategies like weighted averages or minimum scores.

By thoughtfully customizing and combining metrics, you can achieve a comprehensive and meaningful evaluation framework tailored to your unique use case.

## Best Practices for Custom Metric Development

1. **Single Responsibility**: Each metric should evaluate one specific aspect
2. **Clear Definition**: Define precisely what your metric measures
3. **Bounded Output**: Scores should be normalized, typically in [0,1]
4. **Reproducibility**: Minimize randomness in evaluation
5. **Documentation**: Document criteria, prompt design, and interpretation guidelines
6. **Test with Examples**: Verify metric behavior on clear-cut examples
7. **Human Correlation**: Validate that metrics correlate with human judgment

## Standardizing Custom Metrics

To ensure consistency across custom metrics, consider the following best practices:

- Define a clear, human-readable description for each metric.
- Provide interpretation guidelines to help users understand score meanings.
- Include metadata such as metric name, required columns, and output type.
- Use a standardized interface or base class for all custom metrics.

## Implementation Patterns for Advanced Metrics

When developing advanced metrics like topic adherence:

- Design multi-step evaluation workflows for complex tasks.
- Use specialized prompts for different sub-tasks within the metric.
- Allow configurable scoring modes (e.g., precision, recall, F1).
- Support conversational context for multi-turn evaluations.

## Debugging Custom Metrics

Effective debugging strategies include:

- Implementing a debug mode to capture prompt inputs, outputs, and intermediate results.
- Logging detailed evaluation steps for easier troubleshooting.
- Reviewing final scores alongside intermediate calculations to identify issues.


## Conclusion: Building an Evaluation Ecosystem

Custom metrics allow you to build a comprehensive evaluation ecosystem tailored to your application's specific needs:

1. **Baseline metrics**: Start with Ragas' core metrics for fundamental quality aspects
2. **Domain adaptation**: Add specialized metrics for your application domain
3. **Feature-specific metrics**: Develop metrics for unique features of your system
4. **Business alignment**: Create metrics that reflect specific business KPIs and requirements

By extending Ragas with custom metrics, you can create evaluation frameworks that precisely measure what matters most for your LLM applications, leading to more meaningful improvements and better user experiences.

In our next post, we'll explore how to integrate Ragas with popular frameworks and observability tools for seamless evaluation workflows.

---
 
**[Part 1: Introduction to Ragas: The Essential Evaluation Framework for LLM Applications](/blog/introduction-to-ragas/)**  
**[Part 2: Basic Evaluation Workflow](/blog/basic-evaluation-workflow-with-ragas/)**  
**[Part 3: Evaluating RAG Systems with Ragas](/blog/evaluating-rag-systems-with-ragas/)**   
**[Part 4: Test Data Generation](/blog/generating-test-data-with-ragas)**  
**Part 5: Advanced Evaluation Techniques — _You are here_**  
*Next up in the series:*  
**[Part 6: Evaluating AI Agents](/blog/evaluating-ai-agents-with-ragas/)**  
**[Part 7: Integrations and Observability](/blog/integrations-and-observability-with-ragas/)**  
**[Part 8: Building Feedback Loops](/blog/building-feedback-loops-with-ragas/)**  


*How have you implemented feedback loops in your LLM applications? What improvement strategies have been most effective for your use cases? If you’re facing specific evaluation hurdles, don’t hesitate to [reach out](https://www.linkedin.com/in/muhammadafzaal/)—we’d love to help!* 