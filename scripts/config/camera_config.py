import argparse
import configparser

PARSER = argparse.ArgumentParser(description='Run detection on trains.')
PARSER.add_argument('-m', '--model', action='store', default='/usr/share/edgetpu/examples/models/ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite', help="Path to detection model.")
PARSER.add_argument('-l', '--label', action='store', default='/usr/share/edgetpu/examples/models/coco_labels.txt', help="Path to labels text file.")
PARSER.add_argument('-o', '--output_path', action='store', default='/home/coal/Desktop/output/', help="Path to output directory.")
PARSER.add_argument('-W', '--width', type=int, action='store', default=300, help="Capture Width")
PARSER.add_argument('-H', '--height', type=int, action='store', default=300, help="Capture Height")
PARSER.add_argument('-F', '--fps', action='store', type=int, default=60, help="Capture FPS")
PARSER.add_argument('-conf', '--confidence', action='store', type=int, default=20, help="Detection confidence level out of 100.")
PARSER.add_argument('-dts', '--dts', action='store', type=float, default=1, help="distance tracking to stationary.")
PARSER.add_argument('-dds', '--dds', action='store', type=int, default=1, help="distance detect to stationary.")
PARSER.add_argument('-eft', '--eft', action='store', type=int, default=20, help="empty frames allowed for tracking.")
PARSER.add_argument('-efd', '--efd', action='store', type=int, default=40, help="empty frames allowed for detection.")

PARSER.add_argument('-d', '--debug', action='store_true', default=False, help="Debug Mode - Display camera feed")
PARSER.add_argument('-dfps', '--debugonlyfps', action='store_true', default=False, help="Debug Mode - Only FPS")

ARGS = PARSER.parse_args()