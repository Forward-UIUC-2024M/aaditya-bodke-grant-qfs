"""
This module provides a SnippetGenerator class for generating snippets based on grant information and user queries.

The SnippetGenerator uses a BaseClient to interact with an LLM and generate relevant snippets.
It also handles concurrent snippet generation for improved performance.

Classes:
    SnippetGenerator: Main class for generating snippets based on grant information and queries.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Tuple
import re
import os
import logging
from dotenv import load_dotenv
from app.clients.clients import BaseClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Load configuration from environment variables
SNIPPET_GEN_MAX_WORKERS = int(os.getenv('SNIPPET_GEN_MAX_WORKERS', 64))
TEMPERATURE = int(os.getenv('TEMPERATURE', 0.5))


class SnippetGenerator:
    """
    A class for generating snippets based on grant information and user queries.

    Attributes:
        client (BaseClient): The client used for interacting with the LLM.
        model_name (str): The name of the LLM to use.
    """

    def __init__(self, client: BaseClient, model_name: str):
        """
        Initialize the SnippetGenerator.

        Args:
            client (BaseClient): The client used for interacting with the LLM.
            model_name (str): The name of the LLM to use.
        """
        self.client = client
        self.model_name = model_name

    def get_prompt_prefix(self) -> List[Dict[str, str]]:
        """
        Get the prefix for the prompt used in snippet generation.

        Returns:
            List[Dict[str, str]]: A list of message dictionaries forming the prompt prefix.
        """
        return [
            {'role': 'system', 'content': "You are a helpful snippet generator. You are given data (in the format of a dictionary) that describes a grant, and you create a snippet according to the instructions given.\
            Your snippets are accurate, concise, informative and of expert quality. They help the user decide if a grant is worth exploring for their particular interest. \
            You can also give the grant an accurate score based on its relevance to the query, which can be used for ranking different grants."},
            {'role': 'user', 'content': "I want to apply for a grant in an area of my interest. The query describes my interest."},
            {'role': 'assistant', 'content': "Okay, please provide the query and grant information."},
        ]

    def get_prompt_suffix(self) -> List[Dict[str, str]]:
        """
        Get the suffix for the prompt used in snippet generation.

        Returns:
            List[Dict[str, str]]: A list of message dictionaries forming the prompt suffix.
        """
        return [
            {'role': 'assistant', 'content': 'Okay, got the query and grant information.'},
            {'role': 'user', 'content': "Based on the given query and grant information, create a snippet in the form of 2 points -\n\
            1) Grant Summary - A detailed summary of the specific area or activity the grant will fund, that is, the purpose of the grant.\n\
            2) Query Match - A nuanced judgement on whether the grant matches the query. Consider if the grant is for a topic that is closely related to the query, even if it's not an exact match, but do not be too flexible.\n\
            DO NOT start with any prelude like 'Here is a snippet for the grant based on the query:', just get straight to the point. DO NOT number the points.\n\
            DO reuse the headings for the points(Grant Summary and Query Match). DO reply with a newline bewteeen the 2 points. Try to not repeat yourself in different points. The snippet MUST BE 100-120 words or less and COMPLETE.\n\
            Also give the grant a score between 0 to 100, based on the overall relevance to my interest/query. Start your reply with the score between score tags like so <score>value</score>."},
        ]

    
    def construct_prompt(self, query: str, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Construct the full prompt for snippet generation.

        Args:
            query (str): The user's query.
            data (Dict[str, Any]): The grant information.

        Returns:
            List[Dict[str, str]]: The full prompt as a list of message dictionaries.
        """
        prompt = self.get_prompt_prefix()
        fixed_prompt = self.get_prompt_prefix() + self.get_prompt_suffix()
        fixed_tokens = sum(len(self.client.encode(turn['content'])) for turn in fixed_prompt)
        query_tokens = len(self.client.encode(query))

        # truncate data to stay within token limits
        max_data_tokens = self.client.max_input_len - fixed_tokens - query_tokens - 50
        truncated_data = self.truncate_to_token_limit(str(data), max_data_tokens)

        prompt.append({'role': "user", 'content': f'Query - <{query}>\nGrant - <{truncated_data}>'})
        prompt.extend(self.get_prompt_suffix())
        return prompt

    def truncate_to_token_limit(self, text: str, max_tokens: int) -> str:
        """
        Truncate the input text to fit within the specified token limit.

        Args:
            text (str): The input text to truncate.
            max_tokens (int): The maximum number of tokens allowed.

        Returns:
            str: The truncated text.
        """
        tokens = self.client.encode(text)
        if len(tokens) <= max_tokens:
            return text
        return self.client.decode(tokens[:max_tokens])

    def extract_and_remove_score(self, text: str) -> Tuple[Optional[float], str]:
        """
        Extract the score from the generated snippet and remove it from the text.

        Args:
            text (str): The generated snippet text.

        Returns:
            Tuple[Optional[float], str]: The extracted score (normalized to [0, 1]) and the cleaned text.
        """
        match = re.search(r'<score>(.*?)</score>', text)
        if match:
            score = float(match.group(1))
            text = re.sub(r'<score>.*?</score>', '', text)
            return score / 100.0, text
        return None, text

    def _generate_snippet(self, query: str, data: Dict[str, Any]) -> Tuple[str, Optional[float]]:
        """
        Generate a single snippet for the given query and grant data.

        Args:
            query (str): The user's query.
            data (Dict[str, Any]): The grant information.

        Returns:
            Tuple[str, Optional[float]]: The generated snippet and its relevance score.
        """
        messages = self.construct_prompt(query, data)
        try:
            response = self.client.chat(model=self.model_name, messages=messages, temperature=TEMPERATURE)
            score, response = self.extract_and_remove_score(response)
            return response, score
        except Exception as e:
            logger.error(f"Error generating snippet: {str(e)}")
            return "", None

    def _generate_snippets_concurrent(self, tasks: List[Tuple[str, Dict[str, Any]]], max_workers: int = 5) -> List[Tuple[str, Optional[float]]]:
        """
        Generate multiple snippets using concurrently.

        Args:
            tasks (List[Tuple[str, Dict[str, Any]]]): A list of (query, data) tuples.
            max_workers (int, optional): The maximum number of workers. Defaults to 5.

        Returns:
            List[Tuple[str, Optional[float]]]: A list of generated snippets and their scores.
        """
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_task = {executor.submit(self._generate_snippet, query, data): (query, data) for query, data in tasks}
            
            for future in as_completed(future_to_task):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as exc:
                    logger.error(f'Task generated an exception: {exc}')
        
        return results

    def generate_snippets(self, search_results: List[Dict], query: str) -> List[Dict]:
        """
        Generate snippets for a list of search results.

        Args:
            search_results (List[Dict]): A list of search result dictionaries.
            query (str): The user's query.

        Returns:
            List[Dict]: A list of dictionaries containing the generated snippets and related information.
        """
        results = []
        tasks = [(query, {k: v for k, v in result['_source'].items() if k in ['normalized_info']}) for result in search_results]
        snippets = self._generate_snippets_concurrent(tasks, max_workers=SNIPPET_GEN_MAX_WORKERS)
        for (snippet, llm_score), result in zip(snippets, search_results):
            results.append({
                'id': result['_id'],
                'content': result['_source'],
                'snippet': snippet.strip(),
                'es_score': result['_score'],
                'llm_score': llm_score
            })
        return results