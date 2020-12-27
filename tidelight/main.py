from ThreadManager import ThreadManager
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)
logging.info('Starting tide light script')

manager = ThreadManager()
try:
    manager.run()
except KeyboardInterrupt:
    manager.stop()



