"""
Intelligent CSV Reader for PrivateGPT
Replaces default CSV reader with intelligent analysis and narrative generation.
"""

import logging
from pathlib import Path
from typing import Any, List
from datetime import datetime

from llama_index.core.readers.base import BaseReader
from llama_index.core.schema import Document

from private_gpt.components.ingest.csv_processor import csv_processor

logger = logging.getLogger(__name__)


class IntelligentCSVReader(BaseReader):
    """
    Intelligent CSV reader that converts raw CSV data into narrative analysis.
    
    This reader automatically:
    1. Detects the type of CSV data (sensor data, time-series, general data)
    2. Performs appropriate analysis 
    3. Generates intelligent narratives instead of raw CSV text
    4. Creates structured content that LLMs can understand and query effectively
    """

    def load_data(
        self, 
        file: Path, 
        extra_info: dict[str, Any] | None = None,
        **kwargs: Any
    ) -> List[Document]:
        """
        Load CSV file and convert to intelligent narrative document(s).
        
        Args:
            file: Path to the CSV file
            extra_info: Additional metadata (optional)
            **kwargs: Additional arguments (unused)
            
        Returns:
            List of Document objects containing intelligent analysis
        """
        try:
            logger.info(f"Processing CSV file with intelligent analysis: {file}")
            
            # Use our intelligent CSV processor to generate narrative
            narrative_content = csv_processor.process_csv_file(file)
            
            # Create metadata
            metadata = {
                "source_file": str(file),
                "source_type": "csv_analysis",
                "processing_type": "intelligent_narrative",
                "file_size": file.stat().st_size,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            if extra_info:
                metadata.update(extra_info)
            
            # Create document with the intelligent narrative
            document = Document(
                text=narrative_content,
                metadata=metadata
            )
            
            logger.info(f"Successfully converted CSV to intelligent narrative: {len(narrative_content)} characters")
            
            return [document]
            
        except Exception as e:
            logger.error(f"Error processing CSV file {file}: {e}")
            
            # Fallback: Create an error document
            error_content = f"""CSV PROCESSING ERROR
File: {file}
Error: {str(e)}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

The CSV file could not be processed with intelligent analysis.
Please check the file format and try again.
"""
            
            return [Document(
                text=error_content,
                metadata={
                    "source_file": str(file),
                    "source_type": "csv_error",
                    "error": str(e)
                }
            )]
