from pyairtable import Api
import requests
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger("ReelsScraper")

class ReelsScraper:
    def __init__(self, logger):
        self.logger = logger
        self.logger.info("Initializing ReelsScraper")
        
        load_dotenv()
        self.api_key = os.getenv('AIRTABLE_API_KEY')
        self.base_id = os.getenv('AIRTABLE_BASE_ID')
        self.table_name = os.getenv('AIRTABLE_TABLE_NAME')
        self.view_name = 'Faceswapable'

        if not all([self.api_key, self.base_id, self.table_name]):
            self.logger.error("Missing required environment variables")
            raise ValueError("Missing required environment variables")

        try:
            self.airtable = Api(self.api_key)
            self.logger.info(f"Connected to Airtable base: {self.base_id}")
        except Exception as e:
            self.logger.error(f"Failed to connect to Airtable: {str(e)}")
            raise

        self.reels_dir = Path('Reels')
        self.reels_dir.mkdir(exist_ok=True)
        self.logger.info(f"Ensured Reels directory exists at: {self.reels_dir.absolute()}")

    def download_reel(self, url):
        """Download a reel from URL to Reels directory"""
        filename = f"reel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        self.logger.info(f"Starting download of: {filename}")
        filepath = self.reels_dir / filename

        try:
            self.logger.debug(f"Sending GET request to: {url}")
            response = requests.get(url, stream=True)
            response.raise_for_status()

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            self.logger.info(f"Successfully downloaded: {filename}")
            return filepath

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to download {url}: {str(e)}")
            if filepath.exists():
                filepath.unlink()
                self.logger.info(f"Cleaned up partial download: {filename}")
            raise

    def mark_as_downloaded(self, record_id):
        """Mark a record as downloaded in Airtable"""
        try:
            table = self.airtable.table(self.base_id, self.table_name)
            table.update(record_id, {'Downloaded': True})
            self.logger.info(f"Marked record {record_id} as downloaded")
        except Exception as e:
            self.logger.error(f"Failed to mark record as downloaded: {str(e)}")
            raise

    def get_undownloaded_reels(self):
        """Get all undownloaded reels from the Faceswapable view"""
        self.logger.info("Fetching undownloaded reels from Faceswapable view")
        
        try:
            table = self.airtable.table(self.base_id, self.table_name)
            records = table.all(view=self.view_name)
            
            if not records:
                self.logger.info("No records found in Faceswapable view")
                return []

            undownloaded_reels = []
            for record in records:
                if record['fields'].get('Downloaded'):
                    continue
                
                reel_url = record['fields'].get('Reel URL')
                if reel_url:
                    undownloaded_reels.append((record['id'], reel_url))

            self.logger.info(f"Found {len(undownloaded_reels)} undownloaded reels")
            return undownloaded_reels

        except Exception as e:
            self.logger.error(f"Error getting reels: {str(e)}")
            raise

    def process_reels(self):
        """Process all undownloaded reels"""
        self.logger.info("Starting to process reels")
        
        try:
            undownloaded_reels = self.get_undownloaded_reels()
            
            if not undownloaded_reels:
                self.logger.info("No undownloaded reels found to process")
                return 0

            processed_count = 0
            for record_id, reel_url in undownloaded_reels:
                try:
                    self.logger.info(f"Processing reel {processed_count + 1} of {len(undownloaded_reels)}")
                    self.download_reel(reel_url)
                    self.mark_as_downloaded(record_id)
                    processed_count += 1
                except Exception as e:
                    self.logger.error(f"Error processing reel {reel_url}: {str(e)}")
                    # Continue with next reel even if one fails
                    continue
            
            return processed_count

        except Exception as e:
            self.logger.error(f"Error in process_reels: {str(e)}")
            raise

def main():
    logger = setup_logging()
    logger.info("Starting ReelsScraper application")

    try:
        scraper = ReelsScraper(logger)
        processed_count = scraper.process_reels()
        logger.info(f"Successfully processed {processed_count} reels")

    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        raise

if __name__ == "__main__":
    main()
