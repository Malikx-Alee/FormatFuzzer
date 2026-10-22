"""
Main orchestrator module for the learning constraints system.
Coordinates template mining, file processing, the special-file pass, saving and reporting.

See README.md in this directory for the data flow, and KNOWN_ISSUES.md / FIX_PLAN.md for the
history of the behaviour implemented here.
"""
import os
import logging
import signal
import sys
import time

# Add parent directory to path for direct execution
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from .config import Config, GlobalState
    from .parsers import FileParser
    from .mutators import FileMutator
    from .transformers import ResultTransformer
    from .checkpoint import CheckpointManager
    from .parallel import process_files_parallel, get_worker_count
    from .result_saver import ResultSaver
    from .statistics import StatisticsReporter
except ImportError:
    from learning_constraints.config import Config, GlobalState
    from learning_constraints.parsers import FileParser
    from learning_constraints.mutators import FileMutator
    from learning_constraints.transformers import ResultTransformer
    from learning_constraints.checkpoint import CheckpointManager
    from learning_constraints.parallel import process_files_parallel, get_worker_count
    from learning_constraints.result_saver import ResultSaver
    from learning_constraints.statistics import StatisticsReporter


class LearningConstraintsOrchestrator:
    """Main orchestrator class for the learning constraints process."""

    def __init__(self, file_type=None, log_level=logging.INFO, max_files=None, source_dir=None,
                 resume_from_checkpoint=None, workers=None):
        """
        Args:
            file_type (str, optional): File type to process. If None, uses Config.FILE_TYPE
            log_level: Logging level
            max_files (int, optional): Maximum number of *source* files to process
            source_dir (str, optional): Directory of input files. If None, uses Config.DATA_DIR
            resume_from_checkpoint (str, optional): Checkpoint file to resume from. If None and
                Config.RESUME_MODE is True, the latest incomplete checkpoint is used.
            workers (int, optional): Override Config.PARALLEL_WORKERS for this run
        """
        if file_type:
            Config.set_file_type(file_type)
        if workers is not None:
            Config.PARALLEL_WORKERS = workers

        self._is_resuming = False
        checkpoint_path = resume_from_checkpoint

        if Config.RESUME_MODE and checkpoint_path is None:
            _, checkpoint_path = Config.find_latest_checkpoint(file_type)
            if checkpoint_path:
                print(f"Found checkpoint to resume: {checkpoint_path}")

        if checkpoint_path and os.path.exists(checkpoint_path):
            self._is_resuming = True
            checkpoint_info = CheckpointManager.load_checkpoint_info(checkpoint_path)
            log_dir = checkpoint_info.get("log_dir")
            if log_dir and os.path.exists(log_dir):
                Config.restore_log_directory(log_dir)
                for sub in (Config.CURRENT_RESULTS_DIR, Config.CURRENT_ABSTRACTED_DIR, Config.CURRENT_ABSTRACTED_SPECIAL_DIR):
                    os.makedirs(sub, exist_ok=True)
                log_file = Config.LOG_FILE
            else:
                self._is_resuming = False
                log_file = Config.initialize_logging(file_type)
        else:
            log_file = Config.initialize_logging(file_type)

        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.FileHandler(log_file), logging.StreamHandler()]
        )
        self.logger = logging.getLogger(__name__)

        self.max_files = max_files
        self.source_dir = source_dir if source_dir else Config.DATA_DIR

        self.global_state = GlobalState()
        self.parser = FileParser(self.global_state)
        self.mutator = FileMutator(self.global_state)
        self.transformer = ResultTransformer()
        self.result_saver = ResultSaver(self.global_state, self.transformer)
        self.stats_reporter = StatisticsReporter(self.global_state)

        self.checkpoint_manager = CheckpointManager(self.global_state)
        self.checkpoint_manager.set_run_info(self.source_dir, max_files)

        if self._is_resuming and checkpoint_path:
            self.checkpoint_manager.checkpoint_path = checkpoint_path
            if self.checkpoint_manager.load_checkpoint():
                self.checkpoint_manager.completed = False
                self.logger.info(f"Resumed from checkpoint: {checkpoint_path}")
                self.logger.info(f"Previously processed {len(self.checkpoint_manager.processed_files)} files")
            else:
                self.logger.warning("Failed to load checkpoint, starting fresh")
                self._is_resuming = False

        files_info = "all files" if max_files is None else f"up to {max_files} files"
        resume_info = " (RESUMING)" if self._is_resuming else ""
        self.logger.info(f"Initialized Learning Constraints Orchestrator for {Config.FILE_TYPE} files ({files_info}){resume_info}")
        self.logger.info(f"Source directory: {self.source_dir}")
        self.logger.info(f"Fuzzer: {Config.get_fuzzer_executable()}  validator strict: {Config.VALIDATOR_STRICT}")
        self.logger.info(f"Log file: {log_file}")
        self.logger.info(f"Results will be saved to: {Config.CURRENT_RESULTS_DIR}")

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------

    def process_file(self, file_path):
        """Process a single file (parse + mutate) into the orchestrator's global state."""
        try:
            original_byte_ranges, byte_ranges = self.parser.parse_file_structure(file_path)
            if not byte_ranges:
                self.logger.warning(f"No byte ranges found for {file_path}")
                return False
            self.logger.info(f"Found {len(original_byte_ranges)} leaf fields, {len(byte_ranges)} learnable")
            self.mutator.mutate_file_completely(file_path, byte_ranges, original_byte_ranges)
            return True
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {e}")
            return False

    def _list_files(self, directory_path, max_files):
        names = sorted(f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f)))
        if max_files is not None:
            names = names[:max_files]
        return [os.path.join(directory_path, f) for f in names]

    def process_directory(self, directory_path, max_files=None, use_parallel=None):
        """
        Process the files in a directory.

        Args:
            directory_path (str): directory to process
            max_files (int, optional): cap on the number of files (sorted by name); None = all
            use_parallel (bool, optional): force parallel/sequential; None follows PARALLEL_WORKERS

        Returns:
            tuple: (successful_count, total_count, skipped_count, failed_count)
        """
        if not os.path.isdir(directory_path):
            self.logger.error(f"Directory does not exist: {directory_path}")
            return 0, 0, 0, 0

        file_paths = self._list_files(directory_path, max_files)
        if not file_paths:
            self.logger.info(f"No files found in directory: {directory_path}")
            return 0, 0, 0, 0

        limit_info = f" (limited to {max_files})" if max_files is not None else ""
        self.logger.info(f"Processing {len(file_paths)} files{limit_info} from {directory_path}")

        num_workers = get_worker_count()
        should_use_parallel = use_parallel if use_parallel is not None else (num_workers > 1)

        return process_files_parallel(
            file_paths=file_paths,
            file_type=Config.FILE_TYPE,
            main_state=self.global_state,
            checkpoint_manager=self.checkpoint_manager,
            logger=self.logger,
            max_workers=num_workers if should_use_parallel else 1,
        )

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------

    def save_results(self):
        self.result_saver.save_all_results()

    def save_template_results(self, template_values):
        self.result_saver.save_template_values(template_values)

    def transform_results(self, output_suffix="_flattened"):
        """Flatten the saved results. Returns (successful_count, total_count)."""
        try:
            if not Config.CURRENT_RESULTS_DIR:
                self.logger.warning("Log directory not initialized, results not transformed!")
                return 0, 0
            successful, total = self.transformer.transform_results_directory(
                results_dir=Config.CURRENT_RESULTS_DIR, output_suffix=output_suffix)
            if successful == 0:
                self.logger.warning("No files were transformed")
            return successful, total
        except Exception as e:
            self.logger.error(f"Error transforming results: {e}")
            return 0, 0

    def log_crc_values(self):
        self.stats_reporter.log_checksum_algorithms()

    def print_statistics(self, extra=None):
        self.stats_reporter.print_statistics(extra)

    # ------------------------------------------------------------------
    # Interrupt handling
    # ------------------------------------------------------------------

    def _install_signal_handlers(self):
        previous = {}

        def _handler(signum, frame):
            try:
                self.checkpoint_manager.save_checkpoint()
                self.logger.warning(f"Received signal {signum}; checkpoint saved to {self.checkpoint_manager.checkpoint_path}")
            except Exception as e:
                self.logger.error(f"Received signal {signum}; checkpoint could not be saved: {e}")
            raise KeyboardInterrupt

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                previous[sig] = signal.signal(sig, _handler)
            except (ValueError, OSError):
                pass  # not in the main thread
        return previous

    @staticmethod
    def _restore_signal_handlers(previous):
        for sig, handler in previous.items():
            try:
                signal.signal(sig, handler)
            except (ValueError, OSError):
                pass

    # ------------------------------------------------------------------
    # Full run
    # ------------------------------------------------------------------

    def run_complete_process(self):
        """
        Run the complete process: template mining, source files, special files, save, report.

        Returns:
            dict with per-pass counts, stats, timing and ``ok`` (True when the run produced
            results, i.e. at least one file succeeded or every file was already processed).
        """
        start_time = time.time()
        self.logger.info("Starting complete learning constraints process")
        previous_handlers = self._install_signal_handlers()

        try:
            self.logger.info("Mining interesting values from template")
            mined_ok, template_values = self.parser.mine_interesting_values_from_template()
            if mined_ok:
                self.save_template_results(template_values)
            else:
                self.logger.warning("Failed to mine interesting values from template, continuing with file processing")

            self.logger.info(f"Processing files from source directory: {self.source_dir}")
            passed = self.process_directory(self.source_dir, max_files=self.max_files)

            # The special pass is independent of max_files (that limit is for source files only).
            self.logger.info(f"Processing files from abstracted special directory (up to {Config.MAX_SPECIAL_FILES})")
            special = self.process_directory(Config.CURRENT_ABSTRACTED_SPECIAL_DIR, max_files=Config.MAX_SPECIAL_FILES)

            self.checkpoint_manager.failed_count = passed[3] + special[3]
            self.checkpoint_manager.mark_complete()
            self.logger.info("Final checkpoint saved")
        except BaseException:
            # Interrupt or crash: keep whatever was learned so far.
            try:
                self.checkpoint_manager.save_checkpoint()
                self.save_results()
            except Exception as e:
                self.logger.error(f"Could not save state after interruption: {e}")
            raise
        finally:
            self._restore_signal_handlers(previous_handlers)

        self.save_results()
        transform_successful, transform_total = self.transform_results()

        try:
            self.log_crc_values()
        except Exception:
            pass

        total_time = time.time() - start_time
        time_str = self.stats_reporter.format_duration(total_time)

        results = {
            'passed_files': {'successful': passed[0], 'total': passed[1], 'skipped': passed[2], 'failed': passed[3]},
            'special_files': {'successful': special[0], 'total': special[1], 'skipped': special[2], 'failed': special[3]},
            'transformed_files': {'successful': transform_successful, 'total': transform_total},
            'stats': self.global_state.get_stats(),
            'total_time': total_time,
            'total_time_formatted': time_str,
            'resumed': self._is_resuming,
            'ok': passed[0] > 0 or (passed[1] > 0 and passed[2] == passed[1]),
            'log_dir': Config.CURRENT_LOG_DIR,
        }
        self.result_saver.save_run_summary(results)
        self.print_statistics(extra={
            "Source files OK/failed/skipped": f"{passed[0]}/{passed[3]}/{passed[2]}",
            "Special files OK/failed": f"{special[0]}/{special[3]}",
        })

        self.logger.info(f"Learning constraints process completed in {time_str}")
        print(f"\nTotal processing time: {time_str}")
        return results


def main(max_files=None):
    """Minimal entry point (PNG, default directory). Returns a process exit code."""
    try:
        orchestrator = LearningConstraintsOrchestrator(file_type="png", max_files=max_files)
        results = orchestrator.run_complete_process()
        print("\nProcessing complete!" if results['ok'] else "\nProcessing finished but no file succeeded.")
        return 0 if results['ok'] else 2
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
        return 130
    except Exception as e:
        print(f"Error in main process: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
