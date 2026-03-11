from functools import wraps
from pathlib import Path

from huey import SqliteHuey
from huey.api import Task

# --- Huey Configuration ---
# Create a sqlite-backed queue in the output directory
output_dir = Path("output")
output_dir.mkdir(parents=True, exist_ok=True)
db_path = output_dir / "huey_queue.db"

# Initialize Huey instance with SQLite storage
huey = SqliteHuey(filename=str(db_path))

# --- Tasks ---

@huey.task()
def run_extraction_job(query: str, location: str, max_results: int, output_dir: str):
    """
    Background worker task that runs the exact same pipeline 
    as the 'main.py run' command.
    """
    # Import locally to avoid heavy imports when just queuing
    from src.pipeline import run_pipeline
    import json
    
    status_file = Path(output_dir) / "running_status.json"
    status_data = {"status": "running", "query": query, "location": location}
    
    try:
        # Write status file to indicate job is running
        status_file.write_text(json.dumps(status_data, ensure_ascii=False))
        
        # Run the pipeline silently (headless=True)
        import asyncio
        asyncio.run(run_pipeline(
            query=query,
            location=location,
            max_results=max_results,
            output_format="both",
            output_dir=output_dir,
            headless=True
        ))
        return {"status": "success", "query": query, "location": location}
    except Exception as e:
        # Re-raise so Huey registers it as an error
        raise RuntimeError(f"Extraction failed: {str(e)}")
    finally:
        # Clean up status file when done
        if status_file.exists():
            status_file.unlink()
