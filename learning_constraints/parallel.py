"""
Parallel processing module for the learning constraints system.
Each worker processes one file with its own GlobalState; the main process merges the results.
"""
import logging
import math
import multiprocessing
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed, TimeoutError as FutureTimeout
from typing import List, Tuple, Dict, Any, Optional

from .config import Config, GlobalState
from .parsers import FileParser
from .mutators import FileMutator
from .utils import remove_path_from_nested_dict


class FileResultLogger:
    """Appends one line per processed file to processed_success.log / processed_failed.log."""

    def __init__(self, log_dir: str):
        self.log_dir = log_dir
        self.success_file = os.path.join(log_dir, "processed_success.log")
        self.failed_file = os.path.join(log_dir, "processed_failed.log")

        if not os.path.exists(self.success_file):
            with open(self.success_file, 'w') as f:
                f.write("# Successfully processed files\n")
                f.write("# Format: timestamp | file_path | processing_time\n")
                f.write("=" * 80 + "\n")
        if not os.path.exists(self.failed_file):
            with open(self.failed_file, 'w') as f:
                f.write("# Failed/Timed out files\n")
                f.write("# Format: timestamp | file_path | reason | processing_time\n")
                f.write("=" * 80 + "\n")

    def log_success(self, file_path: str, elapsed_time: float):
        with open(self.success_file, 'a') as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {file_path} | {elapsed_time:.2f}s\n")

    def log_failure(self, file_path: str, reason: str, elapsed_time: float):
        with open(self.failed_file, 'a') as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {file_path} | {reason} | {elapsed_time:.2f}s\n")

    def log_timeout(self, file_path: str, timeout_seconds: float):
        with open(self.failed_file, 'a') as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {file_path} | TIMEOUT (>{timeout_seconds:.0f}s) | {timeout_seconds:.2f}s+\n")


def _init_worker():
    """Initialize worker process - keep worker logging quiet."""
    logging.getLogger().setLevel(logging.WARNING)


def process_one_file(file_path: str, state: GlobalState):
    """
    Parse and mutate one file into ``state``.

    Returns:
        tuple: (success, error_message)
    """
    parser = FileParser(state)
    mutator = FileMutator(state)
    original_byte_ranges, byte_ranges = parser.parse_file_structure(file_path)
    if not byte_ranges:
        return False, "No byte ranges found"
    mutator.mutate_file_completely(file_path, byte_ranges, original_byte_ranges)
    return True, None


def _process_single_file(args: Tuple[str, Dict[str, Any], List[str]]) -> Dict[str, Any]:
    """
    Worker entry point: process a single file in a separate process.

    Args:
        args: (file_path, config_snapshot, known_attribute_paths)

    Returns:
        dict with file_path, success, state (serialised GlobalState) and error.
    """
    file_path, config_snapshot, known_attributes = args
    try:
        Config.apply_worker_snapshot(config_snapshot)
        local_state = GlobalState()
        local_state.register_attributes(known_attributes)

        success, error = process_one_file(file_path, local_state)
        return {
            'file_path': file_path,
            'success': success,
            'state': local_state.to_dict() if success else None,
            'error': error,
        }
    except Exception as e:
        return {'file_path': file_path, 'success': False, 'state': None, 'error': str(e)}


# ----------------------------------------------------------------------
# Merging
# ----------------------------------------------------------------------

def merge_global_states(main_state: GlobalState, worker_state_dict: Dict[str, Any]):
    """
    Merge a worker's serialised state into the main GlobalState.

    Blacklists are applied to *leaves only*, by cleaned path, so a struct that shares a name
    with a blacklisted field no longer hides its children (the bug that made parallel runs keep
    only the first worker's values).
    """
    if worker_state_dict is None:
        return

    # Blacklists first, so values the worker learned for a field that is blacklisted anywhere
    # are dropped consistently.
    main_state.blacklisted_by_size.update(worker_state_dict.get('blacklisted_by_size', []))
    main_state.blacklisted_by_count.update(worker_state_dict.get('blacklisted_by_count', []))
    main_state.legacy_blacklisted_names.update(worker_state_dict.get('legacy_blacklisted_names', []))
    main_state.seen_attribute_paths.update(worker_state_dict.get('seen_attribute_paths', []))
    for path, count in worker_state_dict.get('dropped_arrays', {}).items():
        main_state.record_dropped_array(path, count)

    _merge_nested_values(
        main_dict=main_state.nested_values_hex,
        worker_dict=worker_state_dict.get('nested_values_hex', {}),
        is_blacklisted=main_state.is_blacklisted,
    )

    # Values of paths blacklisted by the worker must also leave the main state.
    for path in worker_state_dict.get('blacklisted_by_size', []):
        remove_path_from_nested_dict(main_state.nested_values_hex, path)
    for path in worker_state_dict.get('blacklisted_by_count', []):
        remove_path_from_nested_dict(main_state.nested_values_hex, path)

    worker_checksums = worker_state_dict.get('checksum_algorithms', {})
    for chunk_type, algos in worker_checksums.get('by_chunk_type', {}).items():
        existing = main_state.checksum_algorithms['by_chunk_type'].get(chunk_type, [])
        main_state.checksum_algorithms['by_chunk_type'][chunk_type] = sorted(set(existing) | set(algos))
    main_state.checksum_algorithms['compression_methods'].update(worker_checksums.get('compression_methods', {}))

    main_state.valid_abstractions_count += worker_state_dict.get('valid_abstractions_count', 0)
    main_state.valid_abstractions_special_count += worker_state_dict.get('valid_abstractions_special_count', 0)
    main_state.valid_overwrites_count += worker_state_dict.get('valid_overwrites_count', 0)

    # Workers count unique values per file; the union may exceed the limit.
    _enforce_unique_values_limit(main_state)


def _merge_nested_values(main_dict: dict, worker_dict: dict, is_blacklisted=None, current_path: str = ""):
    """
    Recursively merge nested dictionaries whose leaves are sets (or lists after serialisation).

    Args:
        main_dict: destination
        worker_dict: source
        is_blacklisted: callable(cleaned_path) -> bool, consulted for leaves only
        current_path: path prefix of ``worker_dict``
    """
    for key, value in worker_dict.items():
        path = f"{current_path}~{key}" if current_path else key

        if isinstance(value, dict):
            if key not in main_dict or not isinstance(main_dict[key], dict):
                main_dict[key] = {}
            _merge_nested_values(main_dict[key], value, is_blacklisted, path)
            if not main_dict[key]:
                del main_dict[key]
            continue

        if isinstance(value, (list, set)):
            if is_blacklisted is not None and is_blacklisted(path):
                continue
            if key not in main_dict or not isinstance(main_dict[key], (set, list)):
                main_dict[key] = set()
            elif isinstance(main_dict[key], list):
                main_dict[key] = set(main_dict[key])
            main_dict[key].update(value)
            continue

        # Scalar (should not occur): keep the main value if present.
        main_dict.setdefault(key, value)


def _enforce_unique_values_limit(state: GlobalState, logger: Optional[logging.Logger] = None):
    """Blacklist (by count) merged leaves that exceed MAX_UNIQUE_VALUES_PER_ATTRIBUTE."""
    newly = state.enforce_unique_value_limit()
    if logger:
        for path in newly:
            logger.debug(f"Post-merge blacklist (by count): '{path}' exceeded {Config.MAX_UNIQUE_VALUES_PER_ATTRIBUTE} values")
    return newly


def get_worker_count() -> int:
    """Number of worker processes to use."""
    if Config.PARALLEL_WORKERS is None:
        return multiprocessing.cpu_count()
    return max(1, Config.PARALLEL_WORKERS)


# ----------------------------------------------------------------------
# Drivers
# ----------------------------------------------------------------------

def process_files_parallel(
    file_paths: List[str],
    file_type: str,
    main_state: GlobalState,
    checkpoint_manager,
    logger: logging.Logger,
    max_workers: Optional[int] = None
) -> Tuple[int, int, int, int]:
    """
    Process files in parallel.

    Returns:
        tuple: (successful_count, total_count, skipped_count, failed_count)
    """
    if not file_paths:
        return 0, 0, 0, 0

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
        return 0, len(file_paths), skipped_count, 0

    num_workers = max_workers if max_workers is not None else get_worker_count()
    if num_workers <= 1 or len(files_to_process) == 1:
        return _process_files_sequential(files_to_process, file_type, main_state, checkpoint_manager, logger, skipped_count)

    logger.info(f"Processing {len(files_to_process)} files in parallel with {num_workers} workers")

    result_logger = FileResultLogger(Config.CURRENT_LOG_DIR)
    config_snapshot = Config.worker_snapshot()
    batch_size = Config.PARALLEL_BATCH_SIZE
    file_timeout = Config.PARALLEL_FILE_TIMEOUT

    successful_count = 0
    failed_count = 0
    timeout_count = 0
    total_processed = 0
    total_batches = (len(files_to_process) + batch_size - 1) // batch_size

    for batch_index, batch_start in enumerate(range(0, len(files_to_process), batch_size), 1):
        batch = files_to_process[batch_start:batch_start + batch_size]
        logger.info(f"Processing batch {batch_index}/{total_batches} ({len(batch)} files)")
        batch_start_time = time.time()

        # Snapshot of everything seen so far, so workers do not re-discover known attributes.
        known_attributes = sorted(main_state.seen_attribute_paths)
        batch_timeout = None
        if file_timeout:
            batch_timeout = file_timeout * math.ceil(len(batch) / num_workers) + 60

        executor = ProcessPoolExecutor(max_workers=num_workers, initializer=_init_worker)
        future_to_info = {}
        for file_path in batch:
            future = executor.submit(_process_single_file, (file_path, config_snapshot, known_attributes))
            future_to_info[future] = {'file_path': file_path, 'start_time': time.time()}

        batch_completed = 0
        timed_out = False
        try:
            for future in as_completed(future_to_info, timeout=batch_timeout):
                info = future_to_info[future]
                file_path = info['file_path']
                elapsed = time.time() - info['start_time']
                total_processed += 1
                batch_completed += 1

                try:
                    result = future.result()
                except Exception as e:
                    failed_count += 1
                    logger.error(f"[{batch_completed}/{len(batch)}] Exception processing {file_path} after {elapsed:.1f}s: {e}")
                    result_logger.log_failure(file_path, str(e), elapsed)
                    checkpoint_manager.mark_file_processed(file_path)
                    continue

                if result and result.get('success'):
                    successful_count += 1
                    if result.get('state'):
                        merge_global_states(main_state, result['state'])
                    logger.info(f"[{batch_completed}/{len(batch)}] Processed {file_path} in {elapsed:.1f}s")
                    result_logger.log_success(file_path, elapsed)
                else:
                    failed_count += 1
                    error = result.get('error', 'Unknown error') if result else 'No result'
                    logger.warning(f"[{batch_completed}/{len(batch)}] Failed {file_path} after {elapsed:.1f}s: {error}")
                    result_logger.log_failure(file_path, error, elapsed)

                checkpoint_manager.mark_file_processed(file_path)
        except FutureTimeout:
            timed_out = True
            for future, info in future_to_info.items():
                if future.done():
                    continue
                timeout_count += 1
                failed_count += 1
                total_processed += 1
                logger.error(f"TIMEOUT: {info['file_path']} still running after the batch limit of {batch_timeout:.0f}s - skipping")
                result_logger.log_timeout(info['file_path'], batch_timeout)
                checkpoint_manager.mark_file_processed(info['file_path'])
        finally:
            # On timeout do not wait for the stuck workers; the subprocess timeouts bound them.
            executor.shutdown(wait=not timed_out, cancel_futures=timed_out)

        checkpoint_manager.save_checkpoint()
        logger.info(f"Batch {batch_index} complete in {time.time() - batch_start_time:.1f}s. "
                    f"Progress: {total_processed}/{len(files_to_process)} files")

    if timeout_count > 0:
        logger.warning(f"Total files that timed out: {timeout_count}")
    if failed_count > 0:
        logger.warning(f"Total files that failed: {failed_count} (see {result_logger.failed_file})")

    logger.info(f"Parallel processing complete: {successful_count}/{len(files_to_process)} successful "
                f"(skipped {skipped_count}, failed {failed_count})")
    return successful_count, len(file_paths), skipped_count, failed_count


def _process_files_sequential(
    file_paths: List[str],
    file_type: str,
    main_state: GlobalState,
    checkpoint_manager,
    logger: logging.Logger,
    skipped_count: int
) -> Tuple[int, int, int, int]:
    """
    Process files sequentially in this process.

    Returns:
        tuple: (successful_count, total_count, skipped_count, failed_count)
    """
    logger.info(f"Processing {len(file_paths)} files sequentially")
    result_logger = FileResultLogger(Config.CURRENT_LOG_DIR) if Config.CURRENT_LOG_DIR else None

    successful_count = 0
    failed_count = 0
    for i, file_path in enumerate(file_paths, 1):
        logger.info(f"Processing file {i}/{len(file_paths)}: {file_path}")
        start = time.time()
        try:
            success, error = process_one_file(file_path, main_state)
        except Exception as e:
            success, error = False, str(e)
        elapsed = time.time() - start

        if success:
            successful_count += 1
            if result_logger:
                result_logger.log_success(file_path, elapsed)
        else:
            failed_count += 1
            logger.warning(f"Failed {file_path}: {error}")
            if result_logger:
                result_logger.log_failure(file_path, error or "unknown", elapsed)

        checkpoint_manager.mark_file_processed(file_path)

    logger.info(f"Sequential processing complete: {successful_count}/{len(file_paths)} successful "
                f"(skipped {skipped_count}, failed {failed_count})")
    return successful_count, len(file_paths) + skipped_count, skipped_count, failed_count
