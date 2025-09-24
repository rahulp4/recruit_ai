# file_processor.py

import queue

def process_file(file_path: str, result_queue: queue.Queue):
    """Mock file processing task — replace with real logic."""
    try:
        print(f"[Worker] Processing {file_path}")
        result = f"Processed: {file_path}"
        result_queue.put(("success", file_path, result))
    except Exception as e:
        result_queue.put(("error", file_path, str(e)))
