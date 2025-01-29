import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqGeneration
import logging
from typing import Dict, Any, List
from ..utils.metrics import TOKENS_PROCESSED
from ..core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class SummarizerService:
    def __init__(self):
        """Initialize the summarizer with model and tokenizer."""
        self.device = torch.device("cuda" if torch.cuda.is_available() and settings.ENABLE_GPU else "cpu")
        self._load_model()
        logger.info(f"Initialized summarizer service on device: {self.device}")

    def _load_model(self):
        """Load the model and tokenizer."""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                settings.DEFAULT_MODEL,
                use_fast=True,
                model_max_length=settings.MAX_INPUT_LENGTH
            )
            self.model = AutoModelForSeq2SeqGeneration.from_pretrained(
                settings.DEFAULT_MODEL,
                torch_dtype=torch.float16 if self.device.type == "cuda" else torch.float32,
                low_cpu_mem_usage=True
            ).to(self.device)
            self.model.eval()
            logger.info(f"Model {settings.DEFAULT_MODEL} loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise RuntimeError("Failed to load model.")

    def summarize(self, text: str, params: Dict[str, Any]) -> str:
        """Generate summary for the given text."""
        try:
            inputs = self.tokenizer(
                text,
                max_length=settings.MAX_INPUT_LENGTH,
                truncation=True,
                return_tensors="pt"
            ).to(self.device)

            TOKENS_PROCESSED.labels(model_name=settings.DEFAULT_MODEL).inc(len(inputs["input_ids"][0]))

            with torch.no_grad():
                output_ids = self.model.generate(
                    **inputs,
                    max_length=params.get("max_length", settings.MAX_OUTPUT_LENGTH),
                    min_length=params.get("min_length", 30),
                    num_beams=params.get("num_beams", 4),
                    length_penalty=params.get("length_penalty", 2.0),
                    early_stopping=True,
                    no_repeat_ngram_size=3,
                    do_sample=params.get("do_sample", False),
                    temperature=params.get("temperature", 1.0),
                    top_p=params.get("top_p", 0.9),
                    use_cache=True
                )
            return self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            raise RuntimeError("Summary generation failed.")

    def cleanup(self):
        """Clean up resources."""
        if hasattr(self, "model"):
            del self.model
        if hasattr(self, "tokenizer"):
            del self.tokenizer
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
