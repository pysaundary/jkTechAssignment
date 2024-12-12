#!/bin/bash

# Get the current directory
DIR_PATH=$(pwd)

# Specify the directory where you want to delete .log files
directory_to_search="$DIR_PATH"

# Use the find command to search for .log files and delete them
find "$directory_to_search" -type f -name "*.pyc" -exec rm -f {} \;
find "$directory_to_search" -type f -name "*.csv" -exec rm -f {} \;
find "$directory_to_search" -type f -name "*.log" -exec rm -f {} \;

# Optionally, you can print a message to confirm the deletion
echo "Deleted all .pyc .log and .csv files in $directory_to_search and its subdirectories."
