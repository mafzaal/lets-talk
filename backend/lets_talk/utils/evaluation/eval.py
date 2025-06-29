from langchain_huggingface import HuggingFaceEmbeddings
from ragas import EvaluationDataset, RunConfig, evaluate
from ragas.testset import TestsetGenerator
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import ChatOpenAI
from ragas.metrics import LLMContextRecall, Faithfulness, FactualCorrectness, ResponseRelevancy, ContextEntityRecall, NoiseSensitivity
from lets_talk.shared.config import EMBEDDING_MODEL,SDG_LLM_MODLEL,EVAL_LLM_MODEL

#TODO: need to make more generic

def generate_testset(docs, llm_model = SDG_LLM_MODLEL, embedding_model = EMBEDDING_MODEL, testset_size=100):
    """
    Generate a test set from the provided documents using the TestsetGenerator.

    Args:
        docs (list): A list of documents to generate the test set from.

    Returns:
        dataset: The generated test set.
    """
    # Initialize the generator with the LLM and embedding model
    generator_llm = LangchainLLMWrapper(ChatOpenAI(model=llm_model))
    generator_embeddings = LangchainEmbeddingsWrapper(HuggingFaceEmbeddings(model_name=embedding_model))

    generator = TestsetGenerator(llm=generator_llm, embedding_model=generator_embeddings)
    dataset = generator.generate_with_langchain_docs(docs, testset_size=testset_size)
    
    return dataset


def run_rag_chain(dataset, chain):
  from tqdm import tqdm

  for test_row in tqdm(dataset):
    response = chain.invoke({"question" : test_row.eval_sample.user_input})
    test_row.eval_sample.response = response["response"].content
    test_row.eval_sample.retrieved_contexts = [context.page_content for context in response["context"]]

  return dataset

def run_ragas_evaluation(dataset,llm=EVAL_LLM_MODEL):
  evaluation_dataset = EvaluationDataset.from_pandas(dataset.to_pandas())
  evaluator_llm = LangchainLLMWrapper(ChatOpenAI(model=llm))
  custom_run_config = RunConfig(timeout=360)
  result = evaluate(
      dataset=evaluation_dataset,
      metrics=[LLMContextRecall(), Faithfulness(), FactualCorrectness(), ResponseRelevancy(), ContextEntityRecall(), NoiseSensitivity()],
      llm=evaluator_llm,
      run_config=custom_run_config
  )

  return result