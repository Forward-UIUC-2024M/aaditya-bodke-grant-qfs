"""
This module provides client classes for interacting with various LLM APIs.

It includes a base abstract class and specific implementations for OpenAI, Ollama,
HuggingFace, and Litellm clients. Each client handles API calls, token encoding/decoding,
and implements retry logic for improved reliability.

Classes:
    BaseClient: Abstract base class for LLM clients.
    OpenAIClient: Client for interacting with OpenAI's API.
    OllamaClient: Client for interacting with Ollama's API.
    HFLlamaClient: Client for interacting with HuggingFace's Inference Endpoints.
    LitellmClient: Client for interacting with various APIs using Litellm.

Functions:
    create_client: Factory function to create the appropriate client based on the client type.
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import List, Any, Callable, Dict, Union
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Load configuration from environment variables
MAX_INPUT_LEN = int(os.getenv('MAX_INPUT_LEN', 8192))
MAX_OUTPUT_LEN = int(os.getenv('MAX_OUTPUT_LEN', 2048))
API_TIMEOUT = int(os.getenv('API_TIMEOUT', 30))

class BaseClient(ABC):
    """
    Abstract base class for LLM clients.

    This class defines the common interface and shared functionality
    for all LLM client implementations.

    Attributes:
        api_key (str): The API key for authentication.
        max_input_len (int): Maximum allowed input length in tokens.
        max_output_len (int): Maximum allowed output length in tokens.
    """

    def __init__(self, api_key: str, max_input_len: int = MAX_INPUT_LEN, max_output_len: int = MAX_OUTPUT_LEN):
        """
        Initialize the BaseClient.

        Args:
            api_key (str): The API key for authentication.
            max_input_len (int, optional): Maximum allowed input length in tokens.
            max_output_len (int, optional): Maximum allowed output length in tokens.
        """
        self.api_key: str = api_key
        self.max_input_len: int = max_input_len
        self.max_output_len: int = max_output_len

    @abstractmethod
    def _make_api_call(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """
        Make an API call to the LLM service.

        This method should be implemented by subclasses to handle
        the specifics of each API.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Dict[str, Any]: The response from the API call.

        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """
        raise NotImplementedError("Subclasses must implement _make_api_call method")

    @abstractmethod
    def encode(self, message: str) -> List[int]:
        """
        Encode a message into token IDs.

        Args:
            message (str): The message to encode.

        Returns:
            List[int]: The list of token IDs.

        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """
        raise NotImplementedError("Subclasses must implement encode method")

    @abstractmethod
    def decode(self, tokens: List[int]) -> str:
        """
        Decode token IDs into a human-readable message.

        Args:
            tokens (List[int]): The list of token IDs to decode.

        Returns:
            str: The decoded message.

        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """
        raise NotImplementedError("Subclasses must implement decode method")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=2))
    def _retry_with_tenacity(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Retry a function call with exponential backoff.

        This method uses the tenacity library to implement retry logic
        with exponential backoff.

        Args:
            func (Callable): The function to retry.
            *args: Variable length argument list for the function.
            **kwargs: Arbitrary keyword arguments for the function.

        Returns:
            Any: The result of the function call.

        Raises:
            Exception: If all retry attempts fail.
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in API call: {str(e)}")
            raise

    def chat(self, *args: Any, **kwargs: Any) -> str:
        """
        Initiate a chat interaction with the LLM.

        This method wraps the API call with retry logic for improved reliability.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            str: The response from the LLM.

        Raises:
            Exception: If the API call fails after all retry attempts.
        """
        try:
            response = self._retry_with_tenacity(self._make_api_call, *args, **kwargs)
            return response
        except Exception as e:
            logger.error(f"Chat interaction failed: {str(e)}")
            raise


class OpenAIClient(BaseClient):
    """
    Client for interacting with OpenAI's API.

    This class implements the BaseClient interface for OpenAI's API,
    handling token encoding/decoding and API calls.

    Attributes:
        client (OpenAI): The OpenAI client instance.
        tokenizer (Encoding): The tokenizer for encoding/decoding messages.
    """

    def __init__(self, api_key: str, max_input_len: int = MAX_INPUT_LEN, max_output_len: int = MAX_OUTPUT_LEN):
        """
        Initialize the OpenAIClient.

        Args:
            api_key (str): The OpenAI API key.
            max_input_len (int, optional): Maximum input length. Defaults to MAX_INPUT_LEN.
            max_output_len (int, optional): Maximum output length. Defaults to MAX_OUTPUT_LEN.
        """
        super().__init__(api_key, max_input_len, max_output_len)
        from openai import OpenAI
        from tiktoken import get_encoding
        
        self.client: OpenAI = OpenAI(api_key=self.api_key)
        self.tokenizer = get_encoding("cl100k_base")

    def encode(self, message: str) -> List[int]:
        """
        Encode a message using the tiktoken tokenizer.

        Args:
            message (str): The message to encode.

        Returns:
            List[int]: The list of token IDs.
        """
        return self.tokenizer.encode(message)

    def decode(self, tokens: List[int]) -> str:
        """
        Decode tokens using the tiktoken tokenizer.

        Args:
            tokens (List[int]): The list of token IDs to decode.

        Returns:
            str: The decoded message.
        """
        return self.tokenizer.decode(tokens)

    def _make_api_call(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """
        Make an API call to OpenAI's chat completions endpoint.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Dict[str, Any]: The API response.

        Raises:
            Exception: If the API call fails.
        """
        try:
            completion = self.client.chat.completions.create(
                *args, 
                **kwargs, 
                timeout=API_TIMEOUT, 
                max_tokens=self.max_output_len
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise


class OllamaClient(BaseClient):
    """
    Client for interacting with ollama's API.

    This class implements the BaseClient interface for ollama's API,
    handling token encoding/decoding and API calls.

    Attributes:
        api_base (str): The base URL for the ollama API.
        client (OpenAI): The OpenAI-compatible client instance for ollama.
        tokenizer (AutoTokenizer): The tokenizer for encoding/decoding messages.
    """

    def __init__(self, api_key: str, api_base: str, model_name: str = "Meta-Llama-3.1-8B", 
                 max_input_len: int = MAX_INPUT_LEN, max_output_len: int = MAX_OUTPUT_LEN):
        """
        Initialize the OllamaClient.

        Args:
            api_key (str): The API key for authentication.
            api_base (str): The base URL for the ollama API.
            model_name (str, optional): The name of the model to use. Defaults to "Meta-Llama-3.1-8B".
            max_input_len (int, optional): Maximum input length. Defaults to MAX_INPUT_LEN.
            max_output_len (int, optional): Maximum output length. Defaults to MAX_OUTPUT_LEN.
        """
        super().__init__(api_key, max_input_len, max_output_len)
        from openai import OpenAI
        from transformers import AutoTokenizer

        self.api_base: str = api_base
        self.client: OpenAI = OpenAI(base_url=f"{self.api_base}", api_key=self.api_key)
        self.tokenizer = AutoTokenizer.from_pretrained(f"meta-llama/{model_name}")

    def encode(self, message: str) -> List[int]:
        """
        Encode a message using the llama tokenizer.

        Args:
            message (str): The message to encode.

        Returns:
            List[int]: The list of token IDs.
        """
        return self.tokenizer.encode(message)

    def decode(self, tokens: List[int]) -> str:
        """
        Decode tokens using the llama tokenizer.

        Args:
            tokens (List[int]): The list of token IDs to decode.

        Returns:
            str: The decoded message.
        """
        return self.tokenizer.decode(tokens)

    def _make_api_call(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """
        Make an API call to ollama's chat completions endpoint.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Dict[str, Any]: The API response.

        Raises:
            Exception: If the API call fails.
        """
        try:
            completion = self.client.chat.completions.create(
                *args, 
                **kwargs, 
                timeout=API_TIMEOUT, 
                max_tokens=self.max_output_len
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"ollama API call failed: {str(e)}")
            raise


class HFLlamaClient(BaseClient):
    """
    Client for interacting with HuggingFace's Inference endpoint models.

    This class implements the BaseClient interface for HuggingFace's API,
    handling token encoding/decoding and API calls.

    Attributes:
        api_base (str): The base URL for the HuggingFace inference endpoint.
        client (OpenAI): The OpenAI-compatible client instance for HuggingFace inference endpoint.
        tokenizer (AutoTokenizer): The tokenizer for encoding/decoding messages.
    """

    def __init__(self, api_key: str, api_base: str, model_name: str = "Meta-Llama-3-8B", 
                 max_input_len: int = MAX_INPUT_LEN, max_output_len: int = MAX_OUTPUT_LEN):
        """
        Initialize the HFLlamaClient.

        Args:
            api_key (str): The API key for authentication.
            api_base (str): The base URL for the HuggingFace inference endpoint.
            model_name (str, optional): The name of the model to use. Defaults to "Meta-Llama-3-8B".
            max_input_len (int, optional): Maximum input length. Defaults to MAX_INPUT_LEN.
            max_output_len (int, optional): Maximum output length. Defaults to MAX_OUTPUT_LEN.
        """
        super().__init__(api_key, max_input_len, max_output_len)
        from openai import OpenAI
        from transformers import AutoTokenizer

        self.api_base: str = api_base
        self.client: OpenAI = OpenAI(base_url=f"{self.api_base}", api_key=self.api_key)
        self.tokenizer = AutoTokenizer.from_pretrained(f"meta-llama/{model_name}")

    def encode(self, message: str) -> List[int]:
        """
        Encode a message using the HuggingFace tokenizer.

        Args:
            message (str): The message to encode.

        Returns:
            List[int]: The list of token IDs.
        """
        return self.tokenizer.encode(message)

    def decode(self, tokens: List[int]) -> str:
        """
        Decode tokens using the HuggingFace tokenizer.

        Args:
            tokens (List[int]): The list of token IDs to decode.

        Returns:
            str: The decoded message.
        """
        return self.tokenizer.decode(tokens)

    def _make_api_call(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """
        Make an API call to HuggingFace's chat completions endpoint.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Dict[str, Any]: The API response.

        Raises:
            Exception: If the API call fails.
        """
        try:
            completion = self.client.chat.completions.create(
                *args, 
                **kwargs, 
                timeout=API_TIMEOUT, 
                max_tokens=self.max_output_len
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"HuggingFace API call failed: {str(e)}")
            raise



class LitellmClient(BaseClient):
    """
    Client for interacting with various LLMs using Litellm.

    This class implements the BaseClient interface for Litellm's API,
    handling token encoding/decoding and API calls.

    Attributes:
        api_base (str): The base URL for the Litellm API.
        model_name (str): The name of the model to use.
        tokenizer (AutoTokenizer): The tokenizer for encoding/decoding messages.
    """

    def __init__(self, api_key: str, api_base: str, model_name: str = "meta-llama/Meta-Llama-3-8B", 
                 max_input_len: int = MAX_INPUT_LEN, max_output_len: int = MAX_OUTPUT_LEN):
        """
        Initialize the LitellmClient.

        Args:
            api_key (str): The API key for authentication.
            api_base (str): The base URL for the Litellm API.
            model_name (str, optional): The name of the model to use. Defaults to "meta-llama/Meta-Llama-3-8B".
            max_input_len (int, optional): Maximum input length. Defaults to MAX_INPUT_LEN.
            max_output_len (int, optional): Maximum output length. Defaults to MAX_OUTPUT_LEN.
        """
        super().__init__(api_key, max_input_len, max_output_len)
        from transformers import AutoTokenizer

        self.api_base: str = api_base
        self.model_name: str = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

    def encode(self, message: str) -> List[int]:
        """
        Encode a message using the Litellm tokenizer.

        Args:
            message (str): The message to encode.

        Returns:
            List[int]: The list of token IDs.
        """
        return self.tokenizer.encode(message)

    def decode(self, tokens: List[int]) -> str:
        """
        Decode tokens using the Litellm tokenizer.

        Args:
            tokens (List[int]): The list of token IDs to decode.

        Returns:
            str: The decoded message.
        """
        return self.tokenizer.decode(tokens)

    def _make_api_call(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """
        Make an API call using Litellm.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Dict[str, Any]: The API response.

        Raises:
            Exception: If the API call fails.
        """
        try:
            from litellm import completion
            response = completion(
                model=self.model_name,
                api_key=self.api_key, 
                api_base=self.api_base, 
                *args, 
                **kwargs,
                max_tokens=self.max_output_len,
                request_timeout=API_TIMEOUT
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Litellm API call failed: {str(e)}")
            raise


def create_client(client_type: str, api_key: str, api_base: str = "", model_name: str = "", 
                  max_input_len: int = MAX_INPUT_LEN, max_output_len: int = MAX_OUTPUT_LEN) -> Union[OpenAIClient, OllamaClient, HFLlamaClient, LitellmClient]:
    """
    Factory function to create the appropriate client based on the client type.

    Args:
        client_type (str): The type of client to create ('openai', 'ollama', 'hf_llama', or 'litellm').
        api_key (str): The API key for authentication.
        api_base (str, optional): The base URL for the API (required for Ollama, HFLlama, and Litellm).
        model_name (str, optional): The name of the model to use (required for Ollama, HFLlama, and Litellm).
        max_input_len (int, optional): Maximum input length. Defaults to MAX_INPUT_LEN.
        max_output_len (int, optional): Maximum output length. Defaults to MAX_OUTPUT_LEN.

    Returns:
        Union[OpenAIClient, OllamaClient, HFLlamaClient, LitellmClient]: The appropriate client instance.

    Raises:
        ValueError: If an invalid client type is provided.
    """
    if client_type == 'openai':
        return OpenAIClient(api_key, max_input_len, max_output_len)
    elif client_type == 'ollama':
        return OllamaClient(api_key, api_base, model_name, max_input_len, max_output_len)
    elif client_type == 'hf_llama':
        return HFLlamaClient(api_key, api_base, model_name, max_input_len, max_output_len)
    elif client_type == 'litellm':
        return LitellmClient(api_key, api_base, model_name, max_input_len, max_output_len)
    else:
        raise ValueError(f"Invalid client type: {client_type}")