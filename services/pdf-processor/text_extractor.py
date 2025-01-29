from typing import Dict, List, Optional, Tuple
import fitz  # PyMuPDF
import os
from loguru import logger
from PIL import Image
import io

# Import settings
from config.settings import settings as project_settings
from config.settings import PDFProcessorSettings
service_settings = PDFProcessorSettings()

class PDFTextExtractor:
    """Handles extraction of text from PDF documents with advanced features and error handling."""
    
    def __init__(self, min_text_length: int = None):
        self.min_text_length = min_text_length or service_settings.min_text_length
        self.extract_images = service_settings.extract_images
        self.image_quality = service_settings.image_quality
        logger.info(f"Initialized PDFTextExtractor with min_text_length={self.min_text_length}")

    async def extract_text(self, file_path: str) -> Dict[int, dict]:
        """
        Extracts text and metadata from PDF pages asynchronously.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dict with page numbers as keys and extracted content as values
        """
        try:
            doc = fitz.open(file_path)
            results = {}
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_content = {
                    'text': page.get_text(),
                    'has_images': len(page.get_images()) > 0,
                    'metadata': self._extract_page_metadata(page),
                    'needs_ocr': False
                }
                
                # Check if page needs OCR
                if len(page_content['text'].strip()) < self.min_text_length and page_content['has_images']:
                    page_content['needs_ocr'] = True
                    logger.info(f"Page {page_num} needs OCR: insufficient text length")
                
                if self.extract_images and page_content['has_images']:
                    page_content['images'] = await self._extract_page_images(page)
                    
                results[page_num] = page_content
                
            doc.close()
            return results
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise PDFExtractionError(f"Failed to process PDF: {str(e)}")

    async def _extract_page_images(self, page: fitz.Page) -> List[Dict]:
        """Extracts images from a single page with metadata."""
        images = []
        try:
            for img_index, img in enumerate(page.get_images(full=True)):
                xref = img[0]
                base_image = page.parent.extract_image(xref)
                
                if base_image:
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    image_meta = {
                        'index': img_index,
                        'extension': image_ext,
                        'size': len(image_bytes),
                        'dimensions': self._get_image_dimensions(image_bytes)
                    }
                    
                    # Save image if storage is configured
                    if service_settings.save_images:
                        await self._save_image(image_bytes, image_ext, page.number, img_index)
                    
                    images.append(image_meta)
                    
            return images
            
        except Exception as e:
            logger.error(f"Error extracting images from page: {str(e)}")
            return []

    async def _save_image(self, image_bytes: bytes, ext: str, page_num: int, img_index: int):
        """Saves extracted image to the configured storage location."""
        try:
            image_dir = service_settings.data_dir / "images"
            image_dir.mkdir(exist_ok=True)
            
            image_path = image_dir / f"page_{page_num}_img_{img_index}.{ext}"
            with open(image_path, 'wb') as f:
                f.write(image_bytes)
                
            logger.debug(f"Saved image: {image_path}")
            
        except Exception as e:
            logger.error(f"Error saving image: {str(e)}")

    def _extract_page_metadata(self, page: fitz.Page) -> dict:
        """Extracts detailed metadata from a PDF page."""
        return {
            'rotation': page.rotation,
            'dimensions': {'width': page.rect.width, 'height': page.rect.height},
            'media_box': [float(x) for x in page.mediabox],
            'crop_box': [float(x) for x in page.cropbox],
        }

    def _get_image_dimensions(self, image_bytes: bytes) -> Tuple[int, int]:
        """Gets dimensions of an image from its bytes."""
        img = Image.open(io.BytesIO(image_bytes))
        return img.size

class PDFExtractionError(Exception):
    """Custom exception for PDF extraction errors."""
    pass