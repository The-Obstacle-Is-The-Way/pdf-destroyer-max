import logging
from src.models.neural_merger.merger import NeuralMerger
from src.models.quality_scoring.scorer import QualityScorer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PipelineOrchestrator:
    def __init__(self):
        self.merger = NeuralMerger()
        self.scorer = QualityScorer()
        logger.info("Pipeline Orchestrator initialized")

    def run_pipeline(self, document_data):
        """
        Run the full pipeline process on the provided document data.
        """
        try:
            # Step 1: Merge neural inputs (if applicable)
            merged_data = self.merger.merge_data(document_data)
            logger.info("Data merged successfully")

            # Step 2: Quality scoring
            scored_data = self.scorer.score(merged_data)
            logger.info("Data quality scoring completed")

            # Additional steps can be added here

            return scored_data
        except Exception as e:
            logger.error(f"Pipeline execution failed: {str(e)}")
            raise
