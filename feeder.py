from flask import (Flask, make_response)
from flask_restful import (Api, Resource)
import argparse
import configparser


# imported parameters in .ini file :
# section
ini_api_section             = "Listener"
# parameters in section
ini_api_bind_address        = "BindAddr"
ini_api_bind_port           = "BindPort"


def main():
    # Handling arguments
    """
    args                = get_args()
    debug               = args.debug
    verbose             = args.verbose
    log_file            = args.logfile
    ini_file            = args.inifile
    """

    # Bouchonnage arguments
    debug = False
    verbose = True
    log_file = 'logs/feeder.log'
    ini_file = 'feeder.ini'

    # Logging settings
    global logger
    logger = setup_logging(debug, verbose, log_file)

    # Load configuration
    global config
    config = configparser.RawConfigParser()
    config.read(ini_file)

    # Get parameters from config (.ini file)
    global param
    param = ConfigParameter()

    # Step 4. Start API
    logger.warning("feeder started")
    feeder_listener.run(
        debug=debug,
        host=param.api_bind_address,
        port=param.api_bind_port,
        use_reloader=False
    )


def get_args():
    """
    Supports the command-line arguments listed below.
    """

    parser = argparse.ArgumentParser(description="Run feeder.")
    parser.add_argument('-d', '--debug',
                        required=False,
                        help='Enable debug output',
                        dest='debug',
                        action='store_true')
    parser.add_argument('-v', '--verbose',
                        required=False,
                        help='Enable verbose output',
                        dest='verbose',
                        action='store_true')
    parser.add_argument('-l', '--log-file',
                        required=False,
                        help='File to log to',
                        dest='logfile',
                        type=str,
                        default="feeder.log")
    parser.add_argument('-p', '--ini-file',
                        required=False,
                        help='File that contain parameters',
                        dest='inifile',
                        type=str,
                        default="feeder.ini")
    args = parser.parse_args()
    return args


def setup_logging(debug, verbose, log_file):
    import logging

    if debug:
        log_level = logging.DEBUG
    elif verbose:
        log_level = logging.INFO
    else:
        log_level = logging.WARNING

    logging.basicConfig(filename=log_file, format='%(asctime)s %(levelname)s %(message)s', level=log_level)
    return logging.getLogger(__name__)


def output_txt_response_format(data, code, headers=None):
    resp = make_response(data, code)
    resp.headers.extend(headers or {})
    return resp


class ConfigParameter(object):
    def __init__(self):
        # Initialize Defaults
        self.api_bind_address = '127.0.0.1'
        self.api_bind_port = '80'

        # Get attributes from .ini file
        self.parse_file()

    def parse_file(self):
        logger.info("INI file: get parameters")
        # API
        if config.has_section(ini_api_section):
            # BindAddr
            if config.has_option(ini_api_section, ini_api_bind_address):
                self.api_bind_address = config.get(ini_api_section, ini_api_bind_address)
            if config.has_option(ini_api_section, ini_api_bind_port):
                self.api_bind_port = config.get(ini_api_section, ini_api_bind_port)
        else:
            logger.error("No Listener Section")


class ApiF5(Resource):
    @staticmethod
    def get(feed_list_name):
        # set output format
        logger.info("ApiF5 GET %s" % feed_list_name)
        api.representations.update({'application/json': output_txt_response_format})

        # set simaulated feed list
        feed_list = ["91.165.208.158"]
        feed_list.append("1.1.1.1,,,\n")
        data = ",,,\n".join(feed_list)
        return data, 200


# -------------- API --------------
# listener
feeder_listener = Flask(__name__)
api = Api(feeder_listener)
# F5 format
api.add_resource(ApiF5, '/F5/<feed_list_name>')

# Start program
if __name__ == "__main__":
    main()
