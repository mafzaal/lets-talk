---
title: "Part 6: Evaluating AI Agents: Beyond Simple Answers with Ragas"
date: 2025-04-28T06:00:00-06:00
layout: blog
description: "Learn how to evaluate complex AI agents using Ragas' specialized metrics for goal accuracy, tool call accuracy, and topic adherence to build more reliable and effective agent-based applications."
categories: ["AI", "Agents", "Evaluation", "Ragas", "LLM"]
coverImage: "/images/ai_agent_evaluation.png"   
readingTime: 8
published: true
---

In our previous posts, we've explored how Ragas evaluates RAG systems and enables custom metrics for specialized applications. As LLMs evolve beyond simple question-answering to become powerful AI agents, evaluation needs have grown more sophisticated too. In this post, we'll explore Ragas' specialized metrics for evaluating AI agents that engage in multi-turn interactions, use tools, and work toward specific goals.

## The Challenge of Evaluating AI Agents

Unlike traditional RAG systems, AI agents present unique evaluation challenges:

- **Multi-turn interactions**: Agents maintain context across multiple exchanges
- **Tool usage**: Agents call external tools and APIs to accomplish tasks
- **Goal-oriented behavior**: Success means achieving the user's ultimate objective
- **Boundaries and constraints**: Agents must operate within defined topic boundaries

Standard metrics like faithfulness or answer relevancy don't fully capture these dimensions. Let's explore three specialized metrics Ragas provides for agent evaluation.

## Evaluating AI Agents: Beyond Simple Answers with Ragas

### 1. Goal Accuracy (`agent_goal_accuracy`)

**What it measures:** Did the agent successfully achieve the user's ultimate objective over the course of the interaction?

**How it works:**
This metric analyzes the entire agent workflow (user inputs, AI responses, tool calls).
*   It uses an LLM (`InferGoalOutcomePrompt`) to identify the `user_goal` and the `end_state` (what actually happened).
*   It then compares the `end_state` to either:
    *   A provided `reference` outcome (**`AgentGoalAccuracyWithReference`**).
    *   The inferred `user_goal` (**`AgentGoalAccuracyWithoutReference`**).
*   An LLM (`CompareOutcomePrompt`) determines if the achieved outcome matches the desired one, resulting in a binary score (1 for success, 0 for failure).

**Why it's important:** For task-oriented agents (like booking systems or assistants), success isn't about individual responses but about completing the overall task correctly. This metric directly measures that end-to-end success.

### 2. Tool Call Accuracy (`tool_call_accuracy`)

**What it measures:** Did the agent use the correct tools, in the right order, and with the right arguments?

**How it works:**
This metric compares the sequence and details of tool calls made by the agent against a `reference_tool_calls` list.
*   It checks if the *sequence* of tool names called by the agent aligns with the reference sequence (`is_sequence_aligned`).
*   For each matching tool call, it compares the arguments provided by the agent to the reference arguments, often using a sub-metric like `ExactMatch` (`_get_arg_score`).
*   The final score reflects both the sequence alignment and the argument correctness.

**Why it's important:** Many agents rely on external tools (APIs, databases, etc.). Incorrect tool usage (wrong tool, bad parameters) leads to task failure. This metric pinpoints issues in the agent's interaction with its tools.

### 3. Topic Adherence (`topic_adherence`)

**What it measures:** Did the agent stick to the allowed topics and appropriately handle requests about restricted topics?

**How it works:**
This metric evaluates conversations against a list of `reference_topics`.
*   It extracts the topics discussed in the user's input (`TopicExtractionPrompt`).
*   It checks if the agent refused to answer questions related to specific topics (`TopicRefusedPrompt`).
*   It classifies whether the discussed topics fall within the allowed `reference_topics` (`TopicClassificationPrompt`).
*   Based on these classifications and refusals, it calculates a score (Precision, Recall, or F1) indicating how well the agent adhered to the topic constraints.

**Why it's important:** Ensures agents stay focused, avoid generating content on forbidden subjects (safety, policy), and handle out-of-scope requests gracefully.

## Implementing Agent Evaluation in Practice

Let's look at a practical example of evaluating an AI agent using these metrics:

```python
from ragas.metrics import AgentGoalAccuracyWithoutReference, ToolCallAccuracy, TopicAdherenceScore
from ragas.evaluation import EvaluationDataset
from ragas.dataset_schema import MultiTurnSample
from langchain_openai import ChatOpenAI
from ragas.llms import LangchainLLMWrapper

# Initialize the LLM
evaluator_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o"))

# Example conversation with a travel booking agent
test_data = {
    "user_input": [
        {"role": "user", "content": "I need to book a flight from New York to London next Friday"},
        {"role": "assistant", "content": "I'd be happy to help you book a flight. Let me search for options...", 
         "tool_calls": [{"name": "search_flights", "arguments": {"origin": "NYC", "destination": "LON", "date": "next Friday"}}]},
        {"role": "tool", "name": "search_flights", "content": "Found 5 flights: Flight 1 (Delta, $750), Flight 2 (British Airways, $820)..."},
        {"role": "assistant", "content": "I found several flights from New York to London next Friday. The cheapest option is Delta for $750. Would you like to book this one?"},
        {"role": "user", "content": "Yes, please book the Delta flight"},
        {"role": "assistant", "content": "I'll book that for you now.", 
         "tool_calls": [{"name": "book_flight", "arguments": {"flight_id": "delta_123", "price": "$750"}}]},
        {"role": "tool", "name": "book_flight", "content": "Booking confirmed. Confirmation #: ABC123"},
        {"role": "assistant", "content": "Great news! Your flight is confirmed. Your confirmation number is ABC123. The flight is scheduled for next Friday. Is there anything else you need help with?"}
    ],
    "reference_topics": ["travel", "flight booking", "schedules", "prices"],
    "reference_tool_calls": [
        {"name": "search_flights", "args": {"origin": "NYC", "destination": "LON", "date": "next Friday"}},
        {"name": "book_flight", "args": {"flight_id": "delta_123", "price": "$750"}}
    ]
}

# Create a sample
sample = MultiTurnSample(**test_data)

# Initialize metrics
goal_accuracy = AgentGoalAccuracyWithoutReference(llm=evaluator_llm)
tool_accuracy = ToolCallAccuracy()
topic_adherence = TopicAdherenceScore(llm=evaluator_llm)

# Calculate scores
goal_score = await goal_accuracy.multi_turn_ascore(sample)
tool_score = tool_accuracy.multi_turn_score(sample)
topic_score = await topic_adherence.multi_turn_ascore(sample)

print(f"Goal Accuracy: {goal_score}")
print(f"Tool Call Accuracy: {tool_score}")
print(f"Topic Adherence: {topic_score}")
```

> 💡 **Try it yourself:**  
> Explore the hands-on notebook for agent evaluation:  
> [06_Evaluating_AI_Agents](https://github.com/mafzaal/intro-to-ragas/blob/master/06_Evaluating_AI_Agents.ipynb)

## Advanced Agent Evaluation Techniques

### Combining Metrics for Comprehensive Evaluation

For a complete assessment of agent capabilities, combine multiple metrics:

```python
from ragas import evaluate

results = evaluate(
    dataset,  # Your dataset of agent conversations
    metrics=[
        AgentGoalAccuracyWithoutReference(llm=evaluator_llm),
        ToolCallAccuracy(),
        TopicAdherence(llm=evaluator_llm)
    ]
)
```

## Best Practices for Agent Evaluation

1. **Test scenario coverage:** Include a diverse range of interaction scenarios
2. **Edge case handling:** Test how agents handle unexpected inputs or failures
3. **Longitudinal evaluation:** Track performance over time to identify regressions
4. **Human-in-the-loop validation:** Periodically verify metric alignment with human judgments
5. **Continuous feedback loops:** Use evaluation insights to guide agent improvements

## Conclusion

Evaluating AI agents requires specialized metrics that go beyond traditional RAG evaluation. Ragas' `agent_goal_accuracy`, `tool_call_accuracy`, and `topic_adherence` provide crucial insights into whether an agent can successfully complete tasks, use tools correctly, and stay within designated boundaries.

By incorporating these metrics into your evaluation pipeline, you can build more reliable and effective AI agents that truly deliver on the promise of helpful, goal-oriented AI assistants.

In our next post, we'll explore how to integrate Ragas with popular frameworks and observability tools for seamless evaluation workflows.

---
 
**[Part 1: Introduction to Ragas: The Essential Evaluation Framework for LLM Applications](/blog/introduction-to-ragas/)**  
**[Part 2: Basic Evaluation Workflow](/blog/basic-evaluation-workflow-with-ragas/)**  
**[Part 3: Evaluating RAG Systems with Ragas](/blog/evaluating-rag-systems-with-ragas/)**   
**[Part 4: Test Data Generation](/blog/generating-test-data-with-ragas/)**  
**[Part 5: Advanced Metrics and Customization](/blog/advanced-metrics-and-customization-with-ragas/)**  
**Part 6: Evaluating AI Agents — _You are here_**  
*Next up in the series:*  
**[Part 7: Integrations and Observability](/blog/integrations-and-observability-with-ragas/)**  
**[Part 8: Building Feedback Loops](/blog/building-feedback-loops-with-ragas/)**  

*How are you evaluating your AI agents? What challenges have you encountered in measuring agent performance? If you're facing specific evaluation hurdles, don't hesitate to [reach out](https://www.linkedin.com/in/muhammadafzaal/)—we'd love to help!*