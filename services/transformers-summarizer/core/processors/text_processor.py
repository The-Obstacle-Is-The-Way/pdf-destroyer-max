import re
from typing import List
import logging

logger = logging.getLogger(__name__)

class TextProcessor:
    """
    Handles minimal input validation, preprocessing, and output formatting
    for the summarization pipeline.
    """

    @staticmethod
    def validate_text(text: str, max_length: int = 1024) -> str:
        """
        Validates the input text:
        - Truncates to max_length.
        - Ensures non-empty and properly formatted input.
        """
        try:
            if not text or not text.strip():
                raise ValueError("Input text is empty or invalid.")

            text = text.strip()
            if len(text) > max_length:
                logger.warning(f"Input text exceeds {max_length} characters. Truncating.")
                text = text[:max_length]

            return text
        except Exception as e:
            logger.error(f"Text validation error: {str(e)}")
            raise

    @staticmethod
    def clean_output(summary: str) -> str:
        """
        Postprocesses the model-generated summary:
        - Removes redundant spaces.
        - Capitalizes sentences.
        - Ensures proper sentence-ending punctuation.
        """
        try:
            summary = re.sub(r"\s+", " ", summary).strip()  # Normalize spaces
            
            # Capitalize the first letter of each sentence
            summary = re.sub(r"([.!?])\s*(\w)", lambda m: m.group(1) + " " + m.group(2).capitalize(), summary)
            if summary and not summary[0].isupper():
                summary = summary[0].upper() + summary[1:]  # Capitalize the first letter if not done

            # Ensure proper sentence-ending punctuation
            if summary and summary[-1] not in ".!?":
                summary += "."

            return summary
        except Exception as e:
            logger.error(f"Output cleaning error: {str(e)}")
            raise

    @staticmethod
    def batch_process_texts(texts: List[str], max_length: int = 1024) -> List[str]:
        """
        Validates and processes a batch of input texts.
        """
        try:
            return [TextProcessor.validate_text(text, max_length) for text in texts]
        except Exception as e:
            logger.error(f"Batch processing error: {str(e)}")
            raise

    @staticmethod
    def batch_clean_summaries(summaries: List[str]) -> List[str]:
        """
        Cleans a batch of generated summaries.
        """
        try:
            return [TextProcessor.clean_output(summary) for summary in summaries]
        except Exception as e:
            logger.error(f"Batch summary cleaning error: {str(e)}")
            raise
