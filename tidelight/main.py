from ThreadManager import ThreadManager
print('Starting tide light script')

manager = ThreadManager()
try:
    manager.run()
except KeyboardInterrupt:
    manager.stop()



