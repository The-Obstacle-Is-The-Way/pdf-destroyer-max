# src/services/model_service.py

from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import logging


class SummarizerService:
    def __init__(self, model_name="facebook/bart-large-cnn"):
        """Initialize the summarization service."""
        self.logger = self._setup_logger()
        self.device = 0 if torch.cuda.is_available() else -1  # Use GPU if available
        self.logger.info(f"Device set to {'GPU' if self.device == 0 else 'CPU'}")
        
        try:
            self.logger.info(f"Loading model: {model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            self.pipeline = pipeline("summarization", model=self.model, tokenizer=self.tokenizer, device=self.device)
            self.logger.info(f"Model {model_name} loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load model {model_name}: {e}")
            self.pipeline = None

    def summarize_text(self, text, params=None):
        """Generate a summary for the given text."""
        if not text or not text.strip():
            self.logger.warning("Received empty or invalid text for summarization")
            return "Invalid input. Please provide a valid text."

        try:
            params = params or {}
            min_length = params.get("min_length", 30)
            max_length = params.get("max_length", 130)
            do_sample = params.get("do_sample", False)
            top_k = params.get("top_k", 50)
            top_p = params.get("top_p", 0.95)
            
            self.logger.info(f"Summarizing text with params: {params}")
            summary = self.pipeline(
                text, 
                min_length=min_length, 
                max_length=max_length, 
                do_sample=do_sample, 
                top_k=top_k, 
                top_p=top_p
            )[0]["summary_text"]
            self.logger.info("Summary generated successfully")
            return summary
        except Exception as e:
            self.logger.error(f"Error during summarization: {e}")
            return "An error occurred during summarization. Please try again."

    def is_model_loaded(self):
        """Check if the model pipeline is loaded."""
        return self.pipeline is not None

    def is_gpu_available(self):
        """Check if GPU is available."""
        return torch.cuda.is_available()

    @staticmethod
    def _setup_logger():
        """Set up logging for the service."""
        logger = logging.getLogger("SummarizerService")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
