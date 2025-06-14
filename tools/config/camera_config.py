default_output_path='/media/coal/sickboyT5/post_covid/images/'
default_debug_output_path='/'.join((default_output_path.split('/'))[:-2]) + '/debug/'
import argparse
import configparser

PARSER = argparse.ArgumentParser(description='Run detection on trains.')
PARSER.add_argument('-m', '--model', action='store', default='/usr/share/edgetpu/examples/models/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite', help="Path to detection model.")
PARSER.add_argument('-l', '--label', action='store', default='/usr/share/edgetpu/examples/models/coco_labels.txt', help="Path to labels text file.")
PARSER.add_argument('-W', '--width', type=int, action='store', default=300, help="Capture Width")
PARSER.add_argument('-H', '--height', type=int, action='store', default=300, help="Capture Height")
PARSER.add_argument('-F', '--fps', action='store', type=int, default=60, help="Capture FPS")

# detection/tracking args
PARSER.add_argument('-conf', '--confidence', action='store', type=int, default=30, help="Detection confidence level out of 100.")
PARSER.add_argument('-dts', '--dts', action='store', type=float, default=15, help="distance tracking to stationary.")
PARSER.add_argument('-dds', '--dds', action='store', type=int, default=15, help="distance detect to stationary.")
PARSER.add_argument('-eft', '--eft', action='store', type=int, default=5, help="empty frames allowed for tracking.")
PARSER.add_argument('-efd', '--efd', action='store', type=int, default=40, help="empty frames allowed for detection.")

# logger args
PARSER.add_argument('-moving_trains_conf' , '--moving_trains_conf' , action='store', type=float, default=0.7, help="Logger")
PARSER.add_argument('-empty_frames_limit' , '--empty_frames_limit' , action='store', type=int, default=100, help="Logger")
PARSER.add_argument('-max_stat_entries'   , '--max_stat_entries'   , action='store', type=int, default=2000, help="Logger")
PARSER.add_argument('-max_moving_entries'   , '--max_moving_entries'   , action='store', type=int, default=200, help="Logger")
PARSER.add_argument('-collect_rate_moving', '--collect_rate_moving', action='store', type=float, default=0.1, help="Logger")
PARSER.add_argument('-collect_rate_stat'  , '--collect_rate_stat'  , action='store', type=float, default=0.001, help="Logger")
PARSER.add_argument('-o', '--output_path', action='store', default=default_output_path, help="Path to output directory.")

PARSER.add_argument('-d', '--debug', action='store_true', default=False, help="Debug Mode - Display camera feed")
PARSER.add_argument('-dfps', '--debugonlyfps', action='store_true', default=False, help="Debug Mode - Only FPS")
PARSER.add_argument('-dskipn'  , '--debug_skip_n'  , action='store', type=int, default=1000, help="Capture one frame per skip_n train detects")
PARSER.add_argument('-doutputpath', '--debug_output_path', action='store', default=default_debug_output_path, help="Path to debug output directory.")

PARSER.add_argument('-c', '--caliberate', action='store_true', default=False, help="Debug Mode - Display camera feed without calling logger.")

ARGS = PARSER.parse_args()