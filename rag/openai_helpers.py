import json
import os
from typing import Any, Callable, Dict, Optional, Tuple

import numpy as np
import polars as pl
import tiktoken
from jinja2 import Environment, FileSystemLoader
from openai import OpenAI

from .data_models.batch import BatchRequestMetadata, BatchRequestModel, BatchResponseModel
from .data_models.chat_completions import ChatCompletionsBody, ChatCompletionsMessage, ChatCompletionsRequestModel
from .data_models.embeddings import EmbeddingsRequestModel, EmbeddingsBody


def generate_prompts_from_text_list(texts: list[str], template_path: str, prompt_file_name: str) -> list[str]:
    """
    Generate a list of prompts by filling in text from a list of strings into a Jinja2 template.

    Args:
        texts (List[str]): A list of strings containing the text.
        template_path (str): The path to the directory containing the Jinja2 template file.
        prompt_file_name (str): The name of the Jinja2 template file to be used for generating prompts.

    Returns:
        List[str]: A list of prompts generated by filling in the text into the template.
    """
    environment = Environment(loader=FileSystemLoader(template_path))
    template = environment.get_template(prompt_file_name)

    prompts = []
    for text in texts:
        prompt = template.render(text=text)
        prompts.append(prompt)

    return prompts


def get_num_tokens_from_string(string: str, encoding_name: str) -> int:
    """
    Returns the number of tokens in a text string.

    Args:
        string (str): The input text string to be tokenized.
        encoding_name (str): The name of the encoding to be used for tokenization.

    Returns:
        int: The number of tokens in the given text string based on the specified encoding.
    """
    encoding = tiktoken.encoding_for_model(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def calculate_token_pricing(num_tokens: int, rate_per_million_tokens: float) -> float:
    """
    Calculates the cost based on the number of tokens and the rate in dollars per million tokens.

    Args:
        num_tokens (int): The number of tokens to be used in the calculation.
        rate_per_million (float): The cost rate in dollars per million tokens.

    Returns:
        float: The total cost for the given number of tokens.
    """
    cost = (num_tokens / 1_000_000) * rate_per_million_tokens
    return np.round(cost, 4)


def create_file_path(base_path: str, filename: str, file_count: int) -> str:
    """
    Generate the full file path with a _num suffix.

    Args:
        base_path (str): The base directory or file path.
        filename (str): Custom filename if base_path is a directory.
        file_count (int): The count to append to the filename.

    Returns:
        str: The generated file path with a suffix appended.
    """
    if os.path.isdir(base_path):
        return os.path.join(base_path, f"{filename}_{file_count}.jsonl")
    name, ext = os.path.splitext(base_path)
    return f"{name}_{file_count}{ext}"


def create_chat_completion_request(prompt: str, index: int) -> str:
    """
    Create a chat completion request for the OpenAI API.

    Args:
        prompt (str): The prompt to be sent to the API.
        index (int): The index used to generate a custom ID for the request.

    Returns:
        str: The representation of the chat completion request.
    """
    request = ChatCompletionsRequestModel(
        custom_id=f"prompt_{index}",
        body=ChatCompletionsBody(messages=[ChatCompletionsMessage(role="user", content=prompt)])
    )
    return request.model_dump_json()


def create_embedding_request(text: str, index: int) -> str:
    """
    Create an embedding request for the OpenAI API.

    Args:
        text (str): The text to be sent to the API.
        index (int): The index used to generate a custom ID for the request.

    Returns:
        str: The representation of the embedding request.
    """
    request = EmbeddingsRequestModel(
        custom_id=f"embedding_{index}",
        body=EmbeddingsBody(input=text)
    )
    return request.model_dump_json()


def write_request_chunks(
    jsonl_file, requests: list[str], current_size: int, max_requests: int, max_file_size_bytes: int
) -> Tuple[int, int]:
    """
    Write requests to the JSONL file until request or size limits are reached.

    Args:
        jsonl_file (File): The file object to write the requests to.
        requests (list[str]): The list of preformatted request strings to write.
        current_size (int): The current size of the file in bytes.
        max_requests (int): The maximum number of requests allowed per file.
        max_file_size_bytes (int): The maximum file size allowed in bytes.

    Returns:
        tuple[int, int]: Number of requests written and updated file size.
    """
    requests_written = 0
    for request in requests:
        if requests_written >= max_requests:
            break

        json_request = request + "\n"
        json_request_size = len(json_request)

        if current_size + json_request_size > max_file_size_bytes:
            print(f"File size limit reached: {max_file_size_bytes / (1024 * 1024)} MB.")
            break

        jsonl_file.write(json_request)
        current_size += json_request_size
        requests_written += 1

    return requests_written, current_size


def write_requests_to_jsonl(
    data: list,
    base_output_path: str,
    batch_request_file: str,
    create_request: Callable[[str, int], str],
    max_requests: int = 50000,
    max_file_size_bytes: int = 100 * 1024 * 1024,  # Default 100 MB
) -> None:
    """
    Write API requests (chat completions, embeddings, etc.) to multiple JSONL files,
    ensuring that request and size limits are respected.

    Args:
        data (list): The list of inputs (e.g., prompts or embedding data).
        base_output_path (str): Directory or file path for output JSONL files.
        batch_request_file (str, optional): Custom batch requests filename for files if base_output_path is a directory.
        create_request (Callable): A function to create the request JSONL based on the input data.
        max_requests (int, optional): Maximum number of requests per file. Defaults to 50,000.
        max_file_size_bytes (int, optional): Maximum file size in bytes. Defaults to 100 MB.

    Returns:
        None
    """
    file_count = 1
    total_written = 0
    requests = [create_request(input_data, i) for i, input_data in enumerate(data)]

    while requests:
        current_filename = create_file_path(base_output_path, batch_request_file, file_count)

        try:
            with open(current_filename, "w") as jsonl_file:
                current_size = 0
                requests_written, current_size = write_request_chunks(
                    jsonl_file, requests, current_size, max_requests, max_file_size_bytes
                )
                total_written += requests_written
                requests = requests[requests_written:]
                print(f"Written {requests_written} requests to {current_filename}.")

            file_count += 1
        except IOError as e:
            print(f"Failed to write to {current_filename}: {e}")
            break

    print(f"Total requests written across all files: {total_written}")


def upload_openai_batch_file(client: OpenAI, batch_request_file: str) -> str:
    """
    Uploads a file to OpenAI and returns the file ID.

    Args:
        client (OpenAI): An instance of the OpenAI client.
        batch_request_file (str): Path to the input batch request JSONL file.

    Returns:
        str: The ID of the uploaded file.
    """
    with open(batch_request_file, "rb") as f:
        batch_input_file = client.files.create(file=f, purpose="batch")
    return batch_input_file.id


def create_openai_batch(client: OpenAI, batch_request: BatchRequestModel) -> Dict[str, Any]:
    """
    Creates an OpenAI batch and returns the response.

    Args:
        client (OpenAI): An instance of the OpenAI client.
        batch_request (BatchRequestModel): The batch request.

    Returns:
        Dict[str, Any]: The response from the OpenAI Batch API.
    """
    return client.batches.create(
        input_file_id=batch_request.input_file_id,
        endpoint=batch_request.endpoint,
        completion_window=batch_request.completion_window,
        metadata=batch_request.metadata.model_dump(),
    )


def save_openai_batch_response(batch_response: BatchResponseModel, batch_response_file: str) -> None:
    """
    Saves the batch response to a JSON file.

    Args:
        batch_response (BatchResponseModel): The batch response.
        batch_response_file (str): Path to the output batch response file.

    Returns:
        None
    """
    with open(batch_response_file, "w") as f:
        json.dump(batch_response.model_dump(), f, indent=2)
    print(f"Response saved to {batch_response_file}")


def create_openai_batch_process(
    api_key: str, 
    batch_request_file: str, 
    batch_response_file: str, 
    endpoint: str, 
    description: Optional[str] = None
) -> None:
    """
    Uploads the OpenAI batch request file, initiates an OpenAI batch process to a specified endpoint,
    and saves the OpenAI batch response to a specified file for future reference.

    Args:
        api_key (str): OpenAI API key.
        batch_request_file (str): Path to the input batch request JSONL file.
        batch_response_file (str): Path to the output batch response file.
        endpoint (str): The OpenAI API endpoint to send the batch request (e.g., "/v1/chat/completions" or "/v1/embeddings").
        description (Optional[str]): Description for the batch process.

    Returns:
        None
    """
    client = OpenAI(api_key=api_key)

    try:
        # Upload the batch request file to OpenAI and get the file ID
        batch_input_file_id = upload_openai_batch_file(client, batch_request_file)

        # Create a batch request model with the input file ID and endpoint
        batch_request = BatchRequestModel(
            input_file_id=batch_input_file_id, 
            endpoint=endpoint,
            metadata=BatchRequestMetadata(description=description)
        )

        # Initiate the batch process and get the response
        batch_response = create_openai_batch(client, batch_request)

        # Save the batch response to the specified file
        save_openai_batch_response(batch_response, batch_response_file)

    except Exception as e:
        print(f"An error occurred: {e}")


def get_openai_batch_id_from_json(file_path: str) -> str:
    """
    Reads the JSON file and extracts the OpenAI batch ID.

    Args:
        file_path (str): Path to the JSON file.

    Returns:
        str: The OpenAI batch ID.
    """
    try:
        with open(file_path, 'r') as json_file:
            data = json.load(json_file)
            return data['id']
    except KeyError:
        raise ValueError("The JSON file does not contain a 'batch_id' field.")
    except FileNotFoundError:
        raise FileNotFoundError(f"The file {file_path} was not found.")
    except json.JSONDecodeError:
        raise ValueError(f"The file {file_path} is not a valid JSON file.")


def handle_completed_openai_batch(client: OpenAI, batch_job: Any, output_file: str) -> None:
    """
    Handles a completed OpenAI batch by downloading and saving the output to a file.

    Args:
        client (OpenAI): An instance of the OpenAI client.
        batch_job (Any): The OpenAI batch job object.
        output_file (str): Path to the output file.

    Returns:
        None
    """
    output_file_id = batch_job.output_file_id

    if output_file_id:
        outputs = client.files.content(output_file_id).content

        with open(output_file, "wb") as file:
            file.write(outputs)
        print(f"OpenAI batch job {batch_job.id} output saved to {output_file}")
    else:
        print(f"OpenAI batch job {batch_job.id} completed, but contains no output.")


def check_openai_batch_status(api_key: str, batch_response_file: str, output_file: str) -> None:
    """
    Retrieves the OpenAI batch job status and prints it. If the batch job is completed,
    it handles the output by writing it to a file.

    Args:
        api_key (str): OpenAI API key.
        batch_response_file (str): Path to the batch response file.
        output_file (str): Path to the output file.

    Returns:
        None
    """
    client = OpenAI(api_key=api_key)

    try:
        openai_batch_id = get_openai_batch_id_from_json(batch_response_file)
        openai_batch_job = client.batches.retrieve(openai_batch_id)
        status = openai_batch_job.status

        if status == "completed":
            handle_completed_openai_batch(client, openai_batch_job, output_file)
        else:
            print(f"OpenAI batch job {openai_batch_id} has status: {status}")

    except Exception as e:
        print(f"An error occurred while checking the OpenAI batch job status: {e}")


def read_batch_chat_completions_output_jsonl_to_polars(file_path: str) -> list[dict]:
    """
    Extracts the 'id', 'custom_id', and 'content' columns from a JSON lines file.

    Args:
        file_path (str): The path to the JSON lines (.jsonl) file.

    Returns:
        list[dict]: A list of dictionaries, each containing 'id', 'custom_id', and 'content'.
    """
    results = []

    with open(file_path, 'r') as file:
        for line in file:
            try:
                json_obj = json.loads(line.strip())
                record = {
                    "id": json_obj["id"],
                    "custom_id": json_obj.get("custom_id", None),  # Use .get() to handle missing custom_id
                    "content": json_obj["response"]["body"]["choices"][0]["message"]["content"]
                }
                results.append(record)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error parsing line: {e}")
    
    return pl.DataFrame(results)


def read_batch_embeddings_output_jsonl_to_polars(file_path: str) -> pl.DataFrame:
    """
    Extracts the 'id', 'custom_id', and 'embedding' columns from a JSON lines file.

    Args:
        file_path (str): The path to the JSON lines (.jsonl) file.

    Returns:
        pl.DataFrame: A Polars DataFrame containing 'id', 'custom_id', and 'embedding' columns.
    """
    results = []

    with open(file_path, 'r') as file:
        for line in file:
            try:
                json_obj = json.loads(line.strip())
                record = {
                    "id": json_obj["id"],
                    "custom_id": json_obj.get("custom_id", None),  # Handle missing custom_id gracefully
                    "embedding": json_obj["response"]["body"]["data"][0]["embedding"]  # Extract the embedding
                }
                results.append(record)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error parsing line: {e}")
    
    return pl.DataFrame(results)
