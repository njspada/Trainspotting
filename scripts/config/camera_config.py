default_output_path='/media/jetsonssd/trainspotting/images/'
import argparse
import configparser

PARSER = argparse.ArgumentParser(description='Run detection on trains.')
PARSER.add_argument('-W', '--width', type=int, action='store', default=300, help="Capture Width")
PARSER.add_argument('-H', '--height', type=int, action='store', default=300, help="Capture Height")
PARSER.add_argument('-F', '--fps', action='store', type=int, default=60, help="Capture FPS")
PARSER.add_argument('-D', '--collect_delta', type=int, action='store', default=60, help="Capture interval in seconds")
PARSER.add_argument('-o', '--outputpath', action='store', default=default_output_path, help="Path to output directory.")

ARGS = PARSER.parse_args()