default_output_path='/media/coal/sickboyT5/post_covid/images/'
import argparse
import configparser

PARSER = argparse.ArgumentParser(description='Run detection on trains.')
PARSER.add_argument('-W', '--width', type=int, action='store', default=300, help="Capture Width")
PARSER.add_argument('-H', '--height', type=int, action='store', default=300, help="Capture Height")
PARSER.add_argument('-F', '--fps', action='store', type=int, default=60, help="Capture FPS")
PARSER.add_argument('-D', '--collect_delta', type=int, action='store', default=60, help="Capture interval in seconds")
PARSER.add_argument('-m', '--model', action='store', default='models/custom_mobilenetv2_2class_edgetpu.tflite', help="Relative path to model.")

# Logger parameters

PARSER.add_argument('-o', '--outputpath', action='store', default=default_output_path, help="Path to output directory.")
PARSER.add_argument('-o', '--len_classify_history_deque', action='store', default=10, help="Max length of classification history deque.")
PARSER.add_argument('-o', '--frame_threshold_train_event_off', action='store', default=60, help="Save one in (threshold) frames.")
PARSER.add_argument('-o', '--frame_threshold_train_event_on', action='store', default=10, help="Save one in (threshold) frames.")
PARSER.add_argument('-o', '--frame_threshold_train_event_stationary', action='store', default=60, help="Save one in (threshold) frames.")
PARSER.add_argument('-o', '--classify_history_p_threshold', action='store', default=10, help="Minimum average probability of train.")
PARSER.add_argument('-o', '--max_train_event_time', action='store', default=10, help="Max time for train event on.")

ARGS = PARSER.parse_args()