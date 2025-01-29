from typing import List, Optional, Dict
import re
from loguru import logger
from dataclasses import dataclass

# Import settings
from config.settings import settings as project_settings
from config.settings import PDFProcessorSettings
service_settings = PDFProcessorSettings()

@dataclass
class TextChunk:
    """Represents a chunk of text with metadata."""
    content: str
    page_number: int
    chunk_index: int
    word_count: int
    metadata: Dict = None

class TextChunker:
    """Handles intelligent text chunking with various strategies."""
    
    def __init__(
        self,
        max_chunk_size: int = None,
        min_chunk_size: int = None,
        overlap: int = None,
        respect_paragraphs: bool = True
    ):
        # Use settings with optional override
        self.max_chunk_size = max_chunk_size or service_settings.chunk_size
        self.min_chunk_size = min_chunk_size or (service_settings.chunk_size // 4)
        self.overlap = overlap or (service_settings.chunk_size // 10)
        self.respect_paragraphs = respect_paragraphs
        
        # Get additional settings
        self.batch_size = service_settings.batch_size
        self.cache_enabled = service_settings.enable_cache
        
        logger.info(
            f"Initialized TextChunker with max_chunk_size={self.max_chunk_size}, "
            f"min_chunk_size={self.min_chunk_size}, overlap={self.overlap}"
        )

    async def chunk_document(self, pages_content: Dict[int, dict]) -> List[TextChunk]:
        """
        Chunks document content into manageable pieces while preserving context.
        
        Args:
            pages_content: Dictionary of page numbers and their content
            
        Returns:
            List of TextChunk objects
        """
        chunks = []
        try:
            # Process pages in batches for better memory management
            page_numbers = sorted(pages_content.keys())
            for i in range(0, len(page_numbers), self.batch_size):
                batch_pages = page_numbers[i:i + self.batch_size]
                for page_num in batch_pages:
                    content = pages_content[page_num]
                    if not content.get('text'):
                        logger.warning(f"No text content for page {page_num}")
                        continue
                        
                    page_chunks = await self._process_page(content['text'], page_num)
                    chunks.extend(page_chunks)
            
                # Optional: Save intermediate results if caching is enabled
                if self.cache_enabled and i + self.batch_size < len(page_numbers):
                    await self._cache_chunks(chunks, f"batch_{i}")
            
            logger.info(f"Created {len(chunks)} chunks from document")
            return chunks
            
        except Exception as e:
            logger.error(f"Error chunking document: {str(e)}")
            raise ChunkingError(f"Failed to chunk document: {str(e)}")

    async def _process_page(self, text: str, page_num: int) -> List[TextChunk]:
        """Processes a single page's text into chunks."""
        chunks = []
        
        # Clean and normalize text
        text = self._normalize_text(text)
        
        if self.respect_paragraphs:
            # Split by paragraphs first
            paragraphs = self._split_into_paragraphs(text)
            current_chunk = []
            current_size = 0
            
            for para in paragraphs:
                para_size = len(para.split())
                
                if current_size + para_size > self.max_chunk_size and current_chunk:
                    # Create chunk from accumulated paragraphs
                    chunk_text = " ".join(current_chunk)
                    chunks.append(self._create_chunk(chunk_text, page_num, len(chunks)))
                    
                    # Start new chunk with overlap
                    if self.overlap > 0 and current_chunk:
                        current_chunk = current_chunk[-1:]  # Keep last paragraph
                        current_size = len(current_chunk[0].split())
                    else:
                        current_chunk = []
                        current_size = 0
                
                current_chunk.append(para)
                current_size += para_size
            
            # Handle remaining paragraphs
            if current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append(self._create_chunk(chunk_text, page_num, len(chunks)))
                
        else:
            # Simple word-based chunking
            words = text.split()
            for i in range(0, len(words), self.max_chunk_size - self.overlap):
                chunk_words = words[i:i + self.max_chunk_size]
                if len(chunk_words) >= self.min_chunk_size:
                    chunk_text = " ".join(chunk_words)
                    chunks.append(self._create_chunk(chunk_text, page_num, len(chunks)))
        
        return chunks

    async def _cache_chunks(self, chunks: List[TextChunk], batch_id: str):
        """Caches processed chunks if enabled."""
        if not self.cache_enabled:
            return
            
        try:
            cache_path = service_settings.temp_dir / f"chunks_{batch_id}.json"
            chunk_data = [
                {
                    "content": chunk.content,
                    "page_number": chunk.page_number,
                    "chunk_index": chunk.chunk_index,
                    "word_count": chunk.word_count,
                    "metadata": chunk.metadata
                }
                for chunk in chunks
            ]
            
            async with aiofiles.open(cache_path, 'w') as f:
                await f.write(json.dumps(chunk_data))
                
        except Exception as e:
            logger.error(f"Error caching chunks: {str(e)}")

    def _normalize_text(self, text: str) -> str:
        """Normalizes text by cleaning whitespace and special characters."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        return text.strip()

    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Splits text into paragraphs based on double newlines or other markers."""
        # Split on double newlines and other common paragraph markers
        paragraphs = re.split(r'\n\s*\n|\r\n\s*\r\n|\f', text)
        # Clean resulting paragraphs
        return [p.strip() for p in paragraphs if p.strip()]

    def _create_chunk(self, text: str, page_num: int, chunk_index: int) -> TextChunk:
        """Creates a TextChunk object with metadata."""
        return TextChunk(
            content=text,
            page_number=page_num,
            chunk_index=chunk_index,
            word_count=len(text.split()),
            metadata={
                'start_offset': len(''.join(text.split()[:self.overlap])) if chunk_index > 0 else 0,
                'has_overlap': chunk_index > 0,
                'chunk_size': self.max_chunk_size,
                'overlap_size': self.overlap
            }
        )

class ChunkingError(Exception):
    """Custom exception for text chunking errors."""
    pass