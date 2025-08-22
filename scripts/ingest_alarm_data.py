#!/usr/bin/env python3
"""
Direct ingestion script for processed alarm data.
Uses PrivateGPT's ingestion API to upload files.
"""

import requests
import logging
from pathlib import Path
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PrivateGPTIngester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url.rstrip('/')
        
    def check_server(self):
        """Check if PrivateGPT server is running."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                logger.info("✅ PrivateGPT server is running")
                return True
            else:
                logger.error(f"❌ Server returned status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Cannot connect to PrivateGPT server: {e}")
            return False
    
    def ingest_file(self, file_path):
        """Ingest a single file into PrivateGPT."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"❌ File not found: {file_path}")
            return False
        
        logger.info(f"📤 Uploading {file_path.name}...")
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f, 'text/plain')}
                response = requests.post(f"{self.base_url}/v1/ingest/files", files=files, timeout=300)
            
            if response.status_code == 200:
                logger.info(f"✅ Successfully ingested {file_path.name}")
                return True
            else:
                logger.error(f"❌ Failed to ingest {file_path.name}: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Upload failed for {file_path.name}: {e}")
            return False
    
    def ingest_processed_data(self, processed_dir="processed_data"):
        """Ingest all processed alarm data files."""
        processed_path = Path(processed_dir)
        
        if not processed_path.exists():
            logger.error(f"❌ Processed data directory not found: {processed_path}")
            return False
        
        # Files to ingest
        files_to_ingest = [
            processed_path / "device_analysis_report.txt",
            processed_path / "executive_summary.txt"
        ]
        
        success_count = 0
        for file_path in files_to_ingest:
            if self.ingest_file(file_path):
                success_count += 1
                time.sleep(2)  # Brief pause between uploads
        
        logger.info(f"📊 Ingestion complete: {success_count}/{len(files_to_ingest)} files uploaded")
        
        if success_count == len(files_to_ingest):
            logger.info("🎉 All files successfully ingested into PrivateGPT!")
            logger.info("💡 You can now ask questions like:")
            logger.info("   • 'What is the status of Device 3?'")
            logger.info("   • 'Are there any devices that need maintenance?'")
            logger.info("   • 'Summarize the device monitoring report'")
            logger.info("   • 'What are the operational recommendations?'")
            return True
        else:
            logger.warning("⚠️  Some files failed to ingest. Check the logs above.")
            return False

def main():
    """Main entry point."""
    ingester = PrivateGPTIngester()
    
    # Check if server is running
    if not ingester.check_server():
        logger.error("Please start PrivateGPT server first:")
        logger.error("  cd E:\\rajesh\\ai\\privateGPT")
        logger.error("  python -m private_gpt")
        return
    
    # Ingest processed data
    success = ingester.ingest_processed_data()
    
    if success:
        print("\n" + "="*60)
        print("🎉 SUCCESS! Your alarm data is now in PrivateGPT!")
        print("="*60)
        print("🌐 Open your browser and go to: http://localhost:8001")
        print("💬 Start asking questions about your device data!")
    else:
        print("\n❌ Ingestion failed. Please check the logs above.")

if __name__ == "__main__":
    main()
