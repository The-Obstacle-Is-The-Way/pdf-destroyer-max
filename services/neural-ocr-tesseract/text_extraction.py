# text_extraction.py
import pytesseract
import cv2
import time
import torch
from transformers import LayoutLMv3Processor, LayoutLMv3ForSequenceClassification
from PIL import Image
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

@dataclass
class OCRResult:
    text: str
    confidence: float
    processing_time: float
    layout_info: Optional[List[Dict]] = None

class LayoutLMProcessor:
    def __init__(self, model_name: str = "microsoft/layoutlmv3-base"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.processor = LayoutLMv3Processor.from_pretrained(model_name)
        self.model = LayoutLMv3ForSequenceClassification.from_pretrained(model_name).to(self.device)
        self.logger = logging.getLogger(__name__)

    def process_image(self, image: Image.Image) -> Tuple[List[str], List[Dict]]:
        encoding = self.processor(image, return_tensors="pt", truncation=True)
        encoding = {k: v.to(self.device) for k, v in encoding.items()}
        
        with torch.no_grad():
            outputs = self.model(**encoding)
        
        text_boxes = []
        layout_info = []
        
        for box, score in zip(outputs.bboxes[0], outputs.scores[0]):
            if score > 0.5:
                x1, y1, x2, y2 = box.tolist()
                text_boxes.append(pytesseract.image_to_string(
                    image.crop((x1, y1, x2, y2))
                ))
                layout_info.append({
                    "bbox": [x1, y1, x2, y2],
                    "confidence": float(score)
                })
        
        return text_boxes, layout_info

class EnhancedOCRProcessor:
    def __init__(self):
        self.tesseract_config = "--oem 1 --psm 3"
        self.layoutlm = LayoutLMProcessor()
        self.executor = ThreadPoolExecutor(max_workers=2)

    async def preprocess_image(self, img: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        denoised = cv2.fastNlMeansDenoising(gray)
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary

    async def extract_text(self, img: np.ndarray) -> OCRResult:
        start_time = time.time()
        
        # Parallel processing for both OCR engines
        processed_img = await self.preprocess_image(img)
        pil_image = Image.fromarray(processed_img)
        
        # Run Tesseract and LayoutLM in parallel
        tesseract_future = self.executor.submit(self._run_tesseract, processed_img)
        layoutlm_future = self.executor.submit(self.layoutlm.process_image, pil_image)
        
        # Get results
        tesseract_text, tesseract_conf = tesseract_future.result()
        layoutlm_boxes, layout_info = layoutlm_future.result()
        
        # Merge results
        combined_text = self._merge_results(tesseract_text, layoutlm_boxes)
        combined_conf = (tesseract_conf + sum(d['confidence'] for d in layout_info)) / (1 + len(layout_info))
        
        processing_time = time.time() - start_time
        
        return OCRResult(
            text=combined_text,
            confidence=combined_conf,
            processing_time=processing_time,
            layout_info=layout_info
        )

    def _run_tesseract(self, img: np.ndarray) -> Tuple[str, float]:
        data = pytesseract.image_to_data(img, config=self.tesseract_config, output_type=pytesseract.Output.DICT)
        text = " ".join([word for word in data['text'] if word.strip()])
        conf = sum(data['conf']) / len(data['conf']) if len(data['conf']) > 0 else 0.0
        return text, conf

    def _merge_results(self, tesseract_text: str, layoutlm_boxes: List[str]) -> str:
        """Merge results from both OCR engines with basic deduplication"""
        all_text = [tesseract_text] + layoutlm_boxes
        unique_text = set()
        
        for text in all_text:
            for sentence in text.split('.'):
                sentence = sentence.strip()
                if sentence:
                    unique_text.add(sentence)
        
        return '. '.join(unique_text)