import configparser
import logging

def get_file(_filename):
    """
    Safely read a file.
    Taken from https://fossies.org/linux/fio/t/run-fio-tests.py
    """
    try:
        with open(_filename, "r") as output_file:
            file_data = output_file.read()
        return file_data
    except OSError:
        return False


def parse_fio_config(_filename) -> object or bool:
    conf = configparser.ConfigParser(allow_no_value=True)
    try:
        conf.read(_filename)
        if not conf.has_section('global'):
            logging.error("Config file does not have a [global] section")
            raise ValueError("Config file does not have a [global] section")
        return dict(conf.items('global', raw=True))     # return all of the items in the global section as a dict    
    except configparser.ParsingError :
        logging.error(f"Unable to parse {_filename}: {configparser.ParsingError}")
        raise configparser.ParsingError(f"Unable to parse {_filename}: {configparser.ParsingError}")
