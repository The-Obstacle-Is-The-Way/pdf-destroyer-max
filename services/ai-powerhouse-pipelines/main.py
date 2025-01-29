import logging
from src.orchestration.smart_orchestrator import PipelineOrchestrator
from src.models.neural_merger.merger import NeuralMerger
from src.models.quality_scoring.scorer import QualityScorer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PipelineManager:
    def __init__(self):
        self.orchestrator = PipelineOrchestrator()
        self.merger = NeuralMerger()
        self.scorer = QualityScorer()
        logger.info("Pipeline Manager initialized")

    def process_document(self, document_data):
        """
        Process a document through the AI pipeline
        """
        try:
            # Orchestrate the pipeline steps
            processed_data = self.orchestrator.run_pipeline(document_data)
            return processed_data
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            raise

if __name__ == "__main__":
    manager = PipelineManager()
    logger.info("AI Powerhouse Pipelines service started")