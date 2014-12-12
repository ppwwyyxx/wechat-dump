
import logging
logging.basicConfig(
    format='\033[1;32m[%(asctime)s %(lineno)d@%(filename)s:%(name)s]\033[0m'
    ' %(message)s',
    datefmt='%H:%M:%S', level=logging.INFO)
