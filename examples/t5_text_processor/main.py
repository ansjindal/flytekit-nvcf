import os
import json
import time
import signal
from datetime import datetime, timezone
from dataclasses import dataclass
from threading import Thread
from typing import List, Dict, Optional
from transformers import T5ForConditionalGeneration, T5Tokenizer
import torch

# NVCF provided environment variables
ROOT_OUTPUT_DIR = os.getenv("NVCT_RESULTS_DIR", "/var/task/result")
PROGRESS_FILE = os.getenv("NVCT_PROGRESS_FILE_PATH", ROOT_OUTPUT_DIR + "/progress")
INPUT_MODELS_DIR = os.getenv("INPUT_MODELS_DIR", "/config/models")
INPUT_RESOURCES_DIR = os.getenv("INPUT_RESOURCES_DIR", "/config/resources")

# Task configuration
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "1"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1000"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
MODEL_NAME = os.getenv("MODEL_NAME", "t5-small")

# Task run status
TASK_RUNNING = True

# Global model and tokenizer
model = None
tokenizer = None

def load_model():
    """Load the T5 model and tokenizer."""
    global model, tokenizer
    print(f"Loading model: {MODEL_NAME}")
    tokenizer = T5Tokenizer.from_pretrained(MODEL_NAME)
    model = T5ForConditionalGeneration.from_pretrained(MODEL_NAME)
    if torch.cuda.is_available():
        print("Using GPU")
        model = model.to("cuda")
    print("Model loaded successfully")

@dataclass
class Progress:
    """
    Schema for the progress file that NVCF uses to track task status.

    Attributes:
        taskId: UUID of the task
        percentComplete: Progress percentage (0-100)
        name: Name of the result folder/artifact
        lastUpdatedAt: Timestamp in RFC 3339 Nano format
        metadata: Additional task metadata
    """
    def __init__(self,
                 taskId: str,
                 percentComplete: int,
                 name: str,
                 lastUpdatedAt: str,
                 metadata: dict):
        self.taskId = taskId
        self.percentComplete = percentComplete
        self.name = name
        self.lastUpdatedAt = lastUpdatedAt
        self.metadata = metadata

    def output_to_json(self) -> str:
        return json.dumps(self.__dict__)

def parse_progress_file(progress_file_path: str) -> Progress:
    """Parse the progress file and return a Progress object."""
    with open(progress_file_path, "r") as f:
        content = json.load(f)
        return Progress(**content)

def graceful_termination_handler(_signal, _frame):
    """Handle termination signals gracefully."""
    global TASK_RUNNING
    print(f"Received signal {_signal}, attempting graceful shutdown")
    TASK_RUNNING = False

# Register signal handlers
signal.signal(signal.SIGTERM, graceful_termination_handler)
signal.signal(signal.SIGINT, graceful_termination_handler)

def update_task_progress(percent_complete: int,
                        progress_file_path: str,
                        progress_name: str,
                        metadata: Optional[Dict] = None) -> None:
    """
    Update the progress file to notify NVCF of task status.

    Args:
        percent_complete: Progress percentage (0-100)
        progress_file_path: Path to the progress file
        progress_name: Name of the result folder/artifact
        metadata: Optional additional metadata
    """
    if metadata is None:
        metadata = {}

    progress = Progress(
        taskId=os.getenv("NVCT_TASK_ID", ""),
        percentComplete=percent_complete,
        name=progress_name,
        lastUpdatedAt=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        metadata=metadata
    )

    temp_file = progress_file_path + ".tmp"
    with open(temp_file, 'w') as file:
        file.write(progress.output_to_json())

    try:
        os.rename(temp_file, progress_file_path)
    except Exception as e:
        print(f"Failed to write to progress file: {e}")
        raise e

def heartbeat(progress_file_path: str) -> None:
    """
    Update the progress file timestamp periodically as a heartbeat.
    NVCF requires this to monitor task health.
    """
    while TASK_RUNNING:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        if not os.path.isfile(progress_file_path):
            print("Creating progress file")
            progress = Progress(
                taskId=os.getenv("NVCT_TASK_ID", ""),
                percentComplete=0,
                name="",
                lastUpdatedAt=ts,
                metadata=dict()
            )
            with open(progress_file_path, "w") as f:
                f.write(progress.output_to_json())
        else:
            progress = parse_progress_file(progress_file_path)
            progress.lastUpdatedAt = ts

            temp_file = progress_file_path + ".tmp"
            with open(temp_file, "w") as f:
                f.write(progress.output_to_json())

            try:
                os.rename(temp_file, progress_file_path)
            except Exception as e:
                print(f"Failed to write to progress file: {e}")
                raise e

        print(f"Updated timestamp in progress file {ts}")
        time.sleep(60)

def prepare_input_for_task(text: str, task_type: str) -> str:
    """
    Prepare input text based on task type.

    Args:
        text: Input text to process
        task_type: Type of task (translation, summarization, qa)

    Returns:
        Formatted input text for the model

    Raises:
        ValueError: If task type is unsupported or if QA input format is invalid
    """
    if task_type == "translation":
        return f"translate English to French: {text}"
    elif task_type == "summarization":
        return f"summarize: {text}"
    else:
        raise ValueError(f"Unsupported task type: {task_type}")

def process_text_batch(texts: List[str], task_type: str) -> List[Dict]:
    """
    Process a batch of texts using the T5 model.

    Args:
        texts: List of input texts to process
        task_type: Type of task to perform

    Returns:
        List of processed results with metadata
    """
    results = []
    for text in texts:
        try:
            # Prepare input for the specific task
            formatted_input = prepare_input_for_task(text, task_type)

            # Encode input
            input_ids = tokenizer.encode(
                formatted_input,
                return_tensors="pt",
                max_length=512,
                truncation=True
            )

            # Move input to GPU if available
            if torch.cuda.is_available():
                input_ids = input_ids.to("cuda")

            # Generate output
            outputs = model.generate(
                input_ids,
                max_length=MAX_TOKENS,
                num_beams=4,
                early_stopping=True,
                temperature=TEMPERATURE
            )

            # Decode output
            processed_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

            result = {
                "input_text": text,
                "processed_text": processed_text,
                "metadata": {
                    "model": MODEL_NAME,
                    "task_type": task_type,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "max_tokens": MAX_TOKENS,
                    "temperature": TEMPERATURE,
                    "device": "cuda" if torch.cuda.is_available() else "cpu"
                }
            }
            results.append(result)

        except Exception as e:
            print(f"Error processing text: {e}")
            results.append({
                "input_text": text,
                "error": str(e),
                "metadata": {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "task_type": task_type
                }
            })

    return results

def load_input_texts() -> List[str]:
    """
    Load input texts from the resources directory.

    Returns:
        List of input texts to process
    """
    return [
            "The house is wonderful.",
            "The quick brown fox jumps over the lazy dog. " * 5,
            "What is the capital of France?\nFrance is a country in Western Europe. Its largest city, Paris, is known for its art, fashion, and culture."
    ]


def main():
    """Main task execution function."""
    # Ensure output directory exists
    while not os.path.exists(ROOT_OUTPUT_DIR):
        print(f"Waiting for {ROOT_OUTPUT_DIR} to be created")
        time.sleep(2)

    # Load model
    try:
        load_model()
    except Exception as e:
        print(f"Failed to load model: {e}")
        exit(1)

    # Start heartbeat thread
    t = Thread(target=heartbeat, args=(PROGRESS_FILE,), daemon=True)
    try:
        t.start()
    except Exception as e:
        print(f"Failed to start heartbeat thread: {e}")
        exit(1)

    # Initialize progress tracking
    update_task_progress(1, PROGRESS_FILE, "t5_processing_results", {
        "model": MODEL_NAME,
        "batch_size": BATCH_SIZE,
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE
    })

    try:
        # Load input texts
        input_texts = load_input_texts()
        print(f"Loaded {len(input_texts)} input texts")

        # Process texts in batches
        total_texts = len(input_texts)
        print(f"Total texts: {total_texts}")
        processed_results = []

        for task in ["translation", "summarization"]:
            for i in range(0, total_texts, BATCH_SIZE):
                batch = input_texts[i:i + BATCH_SIZE]
                batch_results = process_text_batch(batch, task)
                processed_results.extend(batch_results)
            print(processed_results)

        update_task_progress(100, PROGRESS_FILE, "t5_processing_results", {
            "total_processed": len(processed_results),
            "status": "completed",
            "model": MODEL_NAME,
            "batch_size": BATCH_SIZE,
            "max_tokens": MAX_TOKENS,
            "temperature": TEMPERATURE
        })

    except Exception as e:
        print(f"Error during processing: {e}")
        update_task_progress(0, PROGRESS_FILE, "t5_processing_results", {
            "error": str(e),
            "status": "failed",
            "model": MODEL_NAME,
            "batch_size": BATCH_SIZE,
            "max_tokens": MAX_TOKENS,
            "temperature": TEMPERATURE
        })
        exit(1)

    exit(0)

if __name__ == "__main__":
    main()
