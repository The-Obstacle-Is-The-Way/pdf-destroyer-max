from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
from loguru import logger

class FileEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            logger.info(f"File created: {event.src_path}")

    def on_modified(self, event):
        if not event.is_directory:
            logger.info(f"File modified: {event.src_path}")

def main():
    # Set up logging
    logger.add("logs/watchdog.log", rotation="1 day")
    logger.info("Starting file monitor service...")

    # Initialize the event handler and observer
    event_handler = FileEventHandler()
    observer = Observer()
    
    # Set the directory to watch (using the mounted volume path)
    path_to_watch = "/app/data/input"  # This should match your docker-compose volume mount
    observer.schedule(event_handler, path_to_watch, recursive=False)
    
    # Start the observer
    observer.start()
    logger.info(f"Watching directory: {path_to_watch}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("File monitor service stopped")
    
    observer.join()

if __name__ == "__main__":
    main()