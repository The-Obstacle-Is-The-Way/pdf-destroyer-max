# smart_orchestrator.py
from typing import Dict, Any, List
import asyncio
from loguru import logger

class SmartOrchestrator:
    def __init__(self):
        self.processors = {}
        self.neural_merger = None
        self.quality_scorer = None
        
    async def register_processor(self, processor: Any):
        """Register a processor with the orchestrator"""
        self.processors[processor.__class__.__name__] = processor
        
    async def process_document(self, file_path: str) -> Dict[int, str]:
        """Process document through registered processors"""
        results = {}
        tasks = []
        
        for processor in self.processors.values():
            task = asyncio.create_task(processor.process(file_path))
            tasks.append(task)
            
        processed_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Merge results using neural merger if available
        if self.neural_merger:
            results = await self.neural_merger.merge_results(processed_results)
        else:
            # Basic merging if no neural merger
            for idx, result in enumerate(processed_results):
                if not isinstance(result, Exception):
                    results[idx] = result
                    
        return results