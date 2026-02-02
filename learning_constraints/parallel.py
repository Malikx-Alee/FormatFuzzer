"""
Parallel processing module for the learning constraints system.
Provides multiprocessing support for parallel file processing.
"""
import logging
import multiprocessing
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed, TimeoutError
from typing import List, Tuple, Dict, Any, Optional

from .config import Config, GlobalState
from .parsers import FileParser
from .mutators import FileMutator
from .utils import clean_attribute_key


class FileResultLogger:
    """Logger for tracking successful and failed file processing."""

    def __init__(self, log_dir: str):
        """
        Initialize the file result logger.

        Args:
            log_dir: Directory to write log files to
        """
        self.log_dir = log_dir
        self.success_file = os.path.join(log_dir, "processed_success.log")
        self.failed_file = os.path.join(log_dir, "processed_failed.log")

        # Create/clear the log files with headers
        with open(self.success_file, 'w') as f:
            f.write("# Successfully processed files\n")
            f.write("# Format: timestamp | file_path | processing_time\n")
            f.write("=" * 80 + "\n")

        with open(self.failed_file, 'w') as f:
            f.write("# Failed/Timed out files\n")
            f.write("# Format: timestamp | file_path | reason | processing_time\n")
            f.write("=" * 80 + "\n")

    def log_success(self, file_path: str, elapsed_time: float):
        """Log a successfully processed file."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(self.success_file, 'a') as f:
            f.write(f"{timestamp} | {file_path} | {elapsed_time:.2f}s\n")

    def log_failure(self, file_path: str, reason: str, elapsed_time: float):
        """Log a failed file."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(self.failed_file, 'a') as f:
            f.write(f"{timestamp} | {file_path} | {reason} | {elapsed_time:.2f}s\n")

    def log_timeout(self, file_path: str, timeout_seconds: float):
        """Log a timed out file."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(self.failed_file, 'a') as f:
            f.write(f"{timestamp} | {file_path} | TIMEOUT (>{timeout_seconds}s) | {timeout_seconds:.2f}s+\n")


def _init_worker():
    """Initialize worker process - suppress logging to avoid interleaved output."""
    # Reduce logging noise from worker processes
    logging.getLogger().setLevel(logging.WARNING)


def _process_single_file(args: Tuple[str, str, Dict[str, str]]) -> Optional[Dict[str, Any]]:
    """
    Worker function to process a single file in a separate process.

    Args:
        args: Tuple of (file_path, file_type, config_paths)
              config_paths contains: CURRENT_LOG_DIR, CURRENT_RESULTS_DIR,
              CURRENT_ABSTRACTED_DIR, CURRENT_ABSTRACTED_SPECIAL_DIR

    Returns:
        Dictionary containing the processing results and state to merge, or None on failure
    """
    file_path, file_type, config_paths = args

    try:
        # Set file type in this process
        Config.set_file_type(file_type)

        # Restore config paths in this worker process
        Config.CURRENT_LOG_DIR = config_paths['CURRENT_LOG_DIR']
        Config.CURRENT_RESULTS_DIR = config_paths['CURRENT_RESULTS_DIR']
        Config.CURRENT_ABSTRACTED_DIR = config_paths['CURRENT_ABSTRACTED_DIR']
        Config.CURRENT_ABSTRACTED_SPECIAL_DIR = config_paths['CURRENT_ABSTRACTED_SPECIAL_DIR']
        Config.LOG_FILE = config_paths.get('LOG_FILE')

        # Create isolated state for this file
        local_state = GlobalState()
        parser = FileParser(local_state)
        mutator = FileMutator(local_state)

        # Parse the file to get byte ranges
        original_byte_ranges, byte_ranges = parser.parse_file_structure(file_path)

        if not byte_ranges:
            return {
                'file_path': file_path,
                'success': False,
                'state': None,
                'error': 'No byte ranges found'
            }

        # Perform mutation on the file
        mutator.mutate_file_completely(file_path, byte_ranges, original_byte_ranges)

        # Return the local state as a serializable dict for merging
        return {
            'file_path': file_path,
            'success': True,
            'state': local_state.to_dict(),
            'error': None
        }

    except Exception as e:
        return {
            'file_path': file_path,
            'success': False,
            'state': None,
            'error': str(e)
        }


def merge_global_states(main_state: GlobalState, worker_state_dict: Dict[str, Any]):
    """
    Merge a worker's state dictionary into the main global state.

    Args:
        main_state: The main GlobalState to merge into
        worker_state_dict: Dictionary representation of worker's GlobalState
    """
    if worker_state_dict is None:
        return

    # Merge nested_values_hex (nested dicts with sets as leaves)
    _merge_nested_values(
        main_state.nested_values_hex,
        worker_state_dict.get('nested_values_hex', {})
    )

    # Merge blacklisted sets
    main_state.blacklisted_by_size.update(
        worker_state_dict.get('blacklisted_by_size', [])
    )
    main_state.blacklisted_by_count.update(
        worker_state_dict.get('blacklisted_by_count', [])
    )

    # Merge checksum_algorithms
    worker_checksums = worker_state_dict.get('checksum_algorithms', {})

    # Merge by_chunk_type
    for chunk_type, algos in worker_checksums.get('by_chunk_type', {}).items():
        if chunk_type not in main_state.checksum_algorithms['by_chunk_type']:
            main_state.checksum_algorithms['by_chunk_type'][chunk_type] = []
        existing = main_state.checksum_algorithms['by_chunk_type'][chunk_type]
        main_state.checksum_algorithms['by_chunk_type'][chunk_type] = sorted(
            set(existing + algos)
        )

    # Merge compression_methods
    main_state.checksum_algorithms['compression_methods'].update(
        worker_checksums.get('compression_methods', {})
    )

    # Add counts
    main_state.valid_abstractions_count += worker_state_dict.get('valid_abstractions_count', 0)
    main_state.valid_abstractions_special_count += worker_state_dict.get('valid_abstractions_special_count', 0)
    main_state.valid_overwrites_count += worker_state_dict.get('valid_overwrites_count', 0)

    # Enforce MAX_UNIQUE_VALUES_PER_ATTRIBUTE limit after merging
    # This is necessary because each worker has isolated state and may not have
    # exceeded the limit individually, but the merged state might exceed it
    _enforce_unique_values_limit(main_state)


def _merge_nested_values(main_dict: dict, worker_dict: dict):
    """
    Recursively merge nested dictionaries where leaves are sets (or lists from serialization).

    Args:
        main_dict: Main nested dictionary to merge into
        worker_dict: Worker's nested dictionary to merge from
    """
    for key, value in worker_dict.items():
        if key not in main_dict:
            # Key doesn't exist in main - add it
            if isinstance(value, list):
                # Convert list back to set
                main_dict[key] = set(value)
            elif isinstance(value, dict):
                # Recursively create nested structure
                main_dict[key] = {}
                _merge_nested_values(main_dict[key], value)
            else:
                main_dict[key] = value
        else:
            # Key exists - need to merge
            if isinstance(value, dict) and isinstance(main_dict[key], dict):
                # Both are dicts - recurse
                _merge_nested_values(main_dict[key], value)
            elif isinstance(value, (list, set)):
                # Value is a collection - merge as set
                if isinstance(main_dict[key], set):
                    if isinstance(value, list):
                        main_dict[key].update(value)
                    else:
                        main_dict[key].update(value)
                else:
                    # Convert to set if not already
                    main_dict[key] = set(main_dict[key]) if isinstance(main_dict[key], list) else {main_dict[key]}
                    main_dict[key].update(value if isinstance(value, set) else set(value))


def _enforce_unique_values_limit(state: GlobalState, logger: Optional[logging.Logger] = None):
    """
    Enforce MAX_UNIQUE_VALUES_PER_ATTRIBUTE limit on the merged state.

    After merging worker states, some attributes may have exceeded the limit
    even though individual workers didn't exceed it. This function checks all
    attributes and blacklists those that exceed the limit.

    Args:
        state: The GlobalState to check and enforce limits on
        logger: Optional logger for debug messages
    """
    max_values = Config.MAX_UNIQUE_VALUES_PER_ATTRIBUTE
    attributes_to_remove = []

    def _check_nested_dict(current_dict: dict, path: str = ""):
        """Recursively check nested dict for sets that exceed the limit."""
        for key, value in current_dict.items():
            current_path = f"{path}~{key}" if path else key

            if isinstance(value, set):
                # This is a leaf node - check the count
                if len(value) > max_values:
                    cleaned_key = clean_attribute_key(current_path)
                    if cleaned_key not in state.blacklisted_by_count:
                        attributes_to_remove.append((current_path, cleaned_key, len(value)))
            elif isinstance(value, dict):
                # Recurse into nested dict
                _check_nested_dict(value, current_path)

    # Check all attributes in nested_values_hex
    _check_nested_dict(state.nested_values_hex)

    # Remove attributes that exceed the limit (add to blacklisted_by_count)
    for full_path, cleaned_key, count in attributes_to_remove:
        state.blacklisted_by_count.add(cleaned_key)
        _remove_attribute_from_nested(state.nested_values_hex, full_path)
        if logger:
            logger.debug(f"Post-merge blacklist (by count): '{cleaned_key}' had {count} values (limit: {max_values})")


def _remove_attribute_from_nested(root: dict, attribute_path: str):
    """
    Remove an attribute from nested_values_hex by its full path.

    Args:
        root: The root nested dictionary
        attribute_path: Full path like "file~chunk~attribute"
    """
    keys = attribute_path.split("~")

    # Navigate to parent and remove the leaf
    current = root
    for key in keys[:-1]:
        if key in current and isinstance(current[key], dict):
            current = current[key]
        else:
            return  # Path doesn't exist

    # Remove the final key
    final_key = keys[-1]
    if final_key in current:
        del current[final_key]


def get_worker_count() -> int:
    """
    Get the number of worker processes to use.

    Returns:
        Number of worker processes
    """
    if Config.PARALLEL_WORKERS is None:
        return multiprocessing.cpu_count()
    return max(1, Config.PARALLEL_WORKERS)


def process_files_parallel(
    file_paths: List[str],
    file_type: str,
    main_state: GlobalState,
    checkpoint_manager,
    logger: logging.Logger,
    max_workers: Optional[int] = None
) -> Tuple[int, int, int]:
    """
    Process multiple files in parallel using multiprocessing.

    Args:
        file_paths: List of file paths to process
        file_type: The file type being processed
        main_state: The main GlobalState to merge results into
        checkpoint_manager: CheckpointManager instance for tracking progress
        logger: Logger instance
        max_workers: Number of worker processes (None = use Config setting)

    Returns:
        Tuple of (successful_count, total_count, skipped_count)
    """
    if not file_paths:
        return 0, 0, 0

    # Filter out already processed files
    files_to_process = []
    skipped_count = 0

    for file_path in file_paths:
        if checkpoint_manager.is_file_processed(file_path):
            logger.info(f"Skipping already processed file: {file_path}")
            skipped_count += 1
        else:
            files_to_process.append(file_path)

    if not files_to_process:
        logger.info(f"All {len(file_paths)} files already processed")
        return 0, len(file_paths), skipped_count

    # Determine worker count
    num_workers = max_workers if max_workers is not None else get_worker_count()

    # If only 1 worker, process sequentially (no multiprocessing overhead)
    if num_workers <= 1:
        return _process_files_sequential(
            files_to_process, file_type, main_state, checkpoint_manager, logger, skipped_count
        )

    logger.info(f"Processing {len(files_to_process)} files in parallel with {num_workers} workers")

    successful_count = 0
    total_processed = 0

    # Collect config paths to pass to workers (these are set in main process only)
    config_paths = {
        'CURRENT_LOG_DIR': Config.CURRENT_LOG_DIR,
        'CURRENT_RESULTS_DIR': Config.CURRENT_RESULTS_DIR,
        'CURRENT_ABSTRACTED_DIR': Config.CURRENT_ABSTRACTED_DIR,
        'CURRENT_ABSTRACTED_SPECIAL_DIR': Config.CURRENT_ABSTRACTED_SPECIAL_DIR,
        'LOG_FILE': Config.LOG_FILE
    }

    # Initialize file result logger for success/failure tracking
    result_logger = FileResultLogger(Config.CURRENT_LOG_DIR)
    logger.info(f"Success/failure logs: {result_logger.success_file}, {result_logger.failed_file}")

    # Prepare arguments for workers
    work_items = [(fp, file_type, config_paths) for fp in files_to_process]

    # Process in batches for checkpointing
    batch_size = Config.PARALLEL_BATCH_SIZE

    # Get timeout setting
    file_timeout = Config.PARALLEL_FILE_TIMEOUT
    timeout_count = 0
    failed_count = 0

    for batch_start in range(0, len(work_items), batch_size):
        batch = work_items[batch_start:batch_start + batch_size]
        batch_num = batch_start // batch_size + 1
        total_batches = (len(work_items) + batch_size - 1) // batch_size

        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} files)")
        batch_start_time = time.time()

        with ProcessPoolExecutor(max_workers=num_workers, initializer=_init_worker) as executor:
            # Submit all tasks in batch and track submission time
            future_to_info = {}
            for item in batch:
                future = executor.submit(_process_single_file, item)
                future_to_info[future] = {
                    'file_path': item[0],
                    'start_time': time.time()
                }

            # Track completed files in this batch
            batch_completed = 0

            # Collect results as they complete
            for future in as_completed(future_to_info):
                info = future_to_info[future]
                file_path = info['file_path']
                elapsed = time.time() - info['start_time']
                total_processed += 1
                batch_completed += 1

                try:
                    # Use timeout for getting result
                    result = future.result(timeout=file_timeout) if file_timeout else future.result()

                    if result and result.get('success'):
                        successful_count += 1
                        # Merge worker state into main state
                        if result.get('state'):
                            merge_global_states(main_state, result['state'])
                        logger.info(f"[{batch_completed}/{len(batch)}] Processed {file_path} in {elapsed:.1f}s")
                        result_logger.log_success(file_path, elapsed)
                    else:
                        error = result.get('error', 'Unknown error') if result else 'No result'
                        logger.warning(f"[{batch_completed}/{len(batch)}] Failed {file_path} after {elapsed:.1f}s: {error}")
                        result_logger.log_failure(file_path, error, elapsed)
                        failed_count += 1

                    # Mark file as processed
                    checkpoint_manager.mark_file_processed(file_path)

                except TimeoutError:
                    timeout_count += 1
                    failed_count += 1
                    logger.error(f"[{batch_completed}/{len(batch)}] TIMEOUT: {file_path} exceeded {file_timeout}s limit - skipping")
                    result_logger.log_timeout(file_path, file_timeout)
                    checkpoint_manager.mark_file_processed(file_path)
                    # Cancel the future if possible
                    future.cancel()

                except Exception as e:
                    failed_count += 1
                    logger.error(f"[{batch_completed}/{len(batch)}] Exception processing {file_path} after {elapsed:.1f}s: {e}")
                    result_logger.log_failure(file_path, str(e), elapsed)
                    checkpoint_manager.mark_file_processed(file_path)

        # Save checkpoint after each batch
        batch_elapsed = time.time() - batch_start_time
        checkpoint_manager.save_checkpoint()
        logger.info(f"Batch {batch_num} complete in {batch_elapsed:.1f}s. Progress: {total_processed}/{len(files_to_process)} files")

    if timeout_count > 0:
        logger.warning(f"Total files that timed out: {timeout_count}")

    if failed_count > 0:
        logger.warning(f"Total files that failed: {failed_count}")
        logger.info(f"See failed files in: {result_logger.failed_file}")

    logger.info(f"Parallel processing complete: {successful_count}/{len(files_to_process)} successful (skipped {skipped_count})")
    logger.info(f"Results logged to: {result_logger.success_file} and {result_logger.failed_file}")
    return successful_count, len(file_paths), skipped_count


def _process_files_sequential(
    file_paths: List[str],
    file_type: str,
    main_state: GlobalState,
    checkpoint_manager,
    logger: logging.Logger,
    skipped_count: int
) -> Tuple[int, int, int]:
    """
    Process files sequentially (fallback when parallel processing is disabled).

    Args:
        file_paths: List of file paths to process
        file_type: The file type being processed
        main_state: The main GlobalState
        checkpoint_manager: CheckpointManager instance
        logger: Logger instance
        skipped_count: Number of already skipped files

    Returns:
        Tuple of (successful_count, total_count, skipped_count)
    """
    logger.info(f"Processing {len(file_paths)} files sequentially")

    parser = FileParser(main_state)
    mutator = FileMutator(main_state)

    successful_count = 0

    for i, file_path in enumerate(file_paths, 1):
        logger.info(f"Processing file {i}/{len(file_paths)}: {file_path}")

        try:
            original_byte_ranges, byte_ranges = parser.parse_file_structure(file_path)

            if byte_ranges:
                mutator.mutate_file_completely(file_path, byte_ranges, original_byte_ranges)
                successful_count += 1
            else:
                logger.warning(f"No byte ranges found for {file_path}")
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")

        checkpoint_manager.mark_file_processed(file_path)

    total_files = len(file_paths) + skipped_count
    logger.info(f"Sequential processing complete: {successful_count}/{len(file_paths)} successful (skipped {skipped_count})")
    return successful_count, total_files, skipped_count
