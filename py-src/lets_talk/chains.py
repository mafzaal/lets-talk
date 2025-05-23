
# from operator import itemgetter
# from lets_talk import config
# from langchain_openai.chat_models import ChatOpenAI
# from langchain_core.prompts import ChatPromptTemplate

# chat_llm = ChatOpenAI(model=config.LLM_MODEL, temperature=config.LLM_TEMPERATURE)

#create a chain to check query tone
# from lets_talk.prompts import query_tone_check_prompt_template


# tone_check_prompt = ChatPromptTemplate.from_template(query_tone_check_prompt_template)

# # Create chain
# tone_check_chain = (
#      tone_check_prompt | chat_llm
    
# )

# from lets_talk.prompts import rude_query_answer_prompt_template

# rude_query_answer_prompt = ChatPromptTemplate.from_template(rude_query_answer_prompt_template)
# # Create chain
# rude_query_answer_chain = (
#      rude_query_answer_prompt | chat_llm
# )