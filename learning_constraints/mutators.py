"""
File mutation module for the learning constraints system.
Contains functions for mutating files through smart abstraction and random overwrites.
"""
import os
import shutil
import subprocess
from .config import Config, GlobalState
from .validators import FileValidator
from .parsers import FileParser
from .utils import overwrite_bytes_randomly


class FileMutator:
    """File mutator class for performing smart abstraction-based mutations and random overwrite mutations."""
    
    def __init__(self, global_state: GlobalState):
        """
        Initialize the mutator with global state.

        Args:
            global_state (GlobalState): The global state object
        """
        self.global_state = global_state
        self.parser = FileParser(global_state)
        self.validator = FileValidator()
    
    def smart_abstraction_mutation(self, file_path, start, end, output_path):
        """
        Perform smart abstraction-based mutation on a specific byte range using the fuzzer.

        Args:
            file_path (str): Path to the input file
            start (int): Start position for mutation
            end (int): End position for mutation
            output_path (str): Path for the output file

        Returns:
            bool: True if smart abstraction mutation was successful, False otherwise
        """
        try:
            result = subprocess.run(
                [
                    Config.get_fuzzer_executable(), 
                    "abstract", 
                    "--targetfile", file_path, 
                    "--targetstart", str(start), 
                    "--targetend", str(end), 
                    output_path
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True
            )
            
            return os.path.exists(output_path) and result.returncode == 0
            
        except Exception as e:
            print(f"Error performing smart abstraction mutation on {file_path} from {start} to {end}: {e}")
            return False
    
    def random_overwrite_mutation(self, file_path, start, end, output_path):
        """
        Perform random overwrite mutation on a specific byte range.

        Args:
            file_path (str): Path to the input file
            start (int): Start position for mutation
            end (int): End position for mutation
            output_path (str): Path for the output file

        Returns:
            bool: True if random overwrite mutation was successful, False otherwise
        """
        try:
            # Copy original file to output path
            shutil.copy(file_path, output_path)
            
            # Perform random overwrite
            overwrite_bytes_randomly(output_path, start, end)
            
            return True
            
        except Exception as e:
            print(f"Error performing random overwrite mutation on {file_path}: {e}")
            return False
    
    def save_special_file(self, source_path, new_attribute, start, end, operation_type="abstract"):
        """
        Save a file that revealed new attributes to the special directory.
        
        Args:
            source_path (str): Path to the source file
            new_attribute (str): The new attribute that was discovered
            start (int): Start position of the operation
            end (int): End position of the operation
            operation_type (str): Type of operation ("abstract" or "overwrite")
            
        Returns:
            str: Path to the saved special file
        """
        filename = f"special_{operation_type}_{new_attribute}_{start}_{end}.{Config.FILE_TYPE}"
        special_file_path = os.path.join(Config.ABSTRACTED_SPECIAL_DIR, filename)
        
        shutil.copy(source_path, special_file_path)
        self.global_state.valid_abstractions_special_count += 1
        
        # print(f"New attributes found in {operation_type} mutation! Saved to {special_file_path}")
        return special_file_path
    
    def process_smart_abstraction_mutation_attempt(self, file_path, start, end, original_attributes):
        """
        Attempt to perform smart abstraction-based mutation and process the results.

        Args:
            file_path (str): Path to the input file
            start (int): Start position for mutation
            end (int): End position for mutation
            original_attributes (set): Set of original file attributes

        Returns:
            bool: True if a valid smart abstraction mutation was created, False otherwise
        """
        output_file = os.path.join(Config.ABSTRACTED_DIR, f"abstracted.{Config.FILE_TYPE}")
        
        for attempt in range(1, Config.MAX_ABSTRACTION_ATTEMPTS + 1):
            try:
                if self.smart_abstraction_mutation(file_path, start, end, output_file):
                    if self.validator.is_valid_file(output_file):
                        # print(f"Valid Smart Abstraction Mutation {Config.FILE_TYPE}")

                        # Parse the mutated file
                        mutated_byte_ranges = self.parser.parse_file_structure(output_file)

                        # Check for new attributes
                        has_new_attrs, new_attr = self.parser.check_for_new_attributes(
                            mutated_byte_ranges, original_attributes
                        )

                        # Save to special directory if new attributes found
                        if has_new_attrs:
                            self.save_special_file(output_file, new_attr, start, end, "smart_abstraction")

                        # Extract bytes from the mutated file
                        self.parser.extract_bytes_from_file(output_file, mutated_byte_ranges)
                        self.global_state.valid_abstractions_count += 1

                        return True
                    else:
                        # print(f"Invalid Smart Abstraction Mutation {Config.FILE_TYPE}")
                        pass

            except Exception as e:
                print(f"Error in smart abstraction mutation attempt {attempt} for {file_path}: {e}")
        
        return False
    
    def process_random_overwrite_mutation_attempt(self, file_path, start, end, original_attributes):
        """
        Attempt to perform random overwrite mutation and process the results.

        Args:
            file_path (str): Path to the input file
            start (int): Start position for mutation
            end (int): End position for mutation
            original_attributes (set): Set of original file attributes

        Returns:
            bool: True if a valid random overwrite mutation was created, False otherwise
        """
        output_file = os.path.join(Config.ABSTRACTED_DIR, f"overwrite.{Config.FILE_TYPE}")
        
        for attempt in range(1, Config.MAX_OVERWRITE_ATTEMPTS + 1):
            try:
                if self.random_overwrite_mutation(file_path, start, end, output_file):
                    if self.validator.is_valid_file(output_file):
                        # print(f"Valid Random Overwrite Mutation {Config.FILE_TYPE}")

                        # Parse the mutated file
                        mutated_byte_ranges = self.parser.parse_file_structure(output_file)

                        # Check for new attributes
                        has_new_attrs, new_attr = self.parser.check_for_new_attributes(
                            mutated_byte_ranges, original_attributes
                        )

                        # Save to special directory if new attributes found
                        if has_new_attrs:
                            self.save_special_file(output_file, new_attr, start, end, "random_overwrite")

                        # Extract bytes from the mutated file
                        self.parser.extract_bytes_from_file(output_file, mutated_byte_ranges)
                        self.global_state.valid_overwrites_count += 1

                        # Clean up temporary file
                        if os.path.exists(output_file):
                            os.remove(output_file)

                        return True
                    else:
                        # print(f"Invalid Random Overwrite Mutation {Config.FILE_TYPE}")
                        pass

            except Exception as e:
                print(f"Error in random overwrite mutation attempt {attempt} for {file_path}: {e}")
            finally:
                # Clean up temporary file
                if os.path.exists(output_file):
                    os.remove(output_file)
        
        return False
    
    def mutate_file_completely(self, file_path, byte_ranges):
        """
        Perform complete mutation process on a file for all byte ranges using both mutation strategies.

        Args:
            file_path (str): Path to the file to mutate
            byte_ranges (list): List of tuples (start, end, attribute)

        Returns:
            list: The original byte ranges (for compatibility)
        """
        # Get original attributes before mutation
        original_attributes = self.parser.get_file_attributes(byte_ranges)

        for start, end, attribute in byte_ranges:
            # print(f"Mutating {file_path} from {start} to {end}...")

            # Try smart abstraction-based mutation
            try:
                self.process_smart_abstraction_mutation_attempt(file_path, start, end, original_attributes)
            except Exception as e:
                print(f"Error in smart abstraction mutation for {file_path}: {e}")

            # Try random overwrite mutation
            try:
                self.process_random_overwrite_mutation_attempt(file_path, start, end, original_attributes)
            except Exception as e:
                print(f"Error in random overwrite mutation for {file_path}: {e}")

        return byte_ranges



