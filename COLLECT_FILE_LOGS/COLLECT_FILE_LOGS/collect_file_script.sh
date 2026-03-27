#!/bin/bash

set -e // stop the script if one of those scripts are bugging

echo "Start extract the opened and closed file in window_changes.log..."
./extract_window_events.sh
echo "Opened_file.txt and Closed_file.txt successfully extracted!"

# echo "Start correct closed and opened file..."
# python3 correct_opened-closed_file.py
# echo "Format successfully corrected!"

echo "Start create collected_file.txt"
python3 get_collect_file.py
echo "collect_file.txt successfuly created!"

echo "Start to make the real data"
python3 duration_file.py
echo "data_file.txt successfully created!"