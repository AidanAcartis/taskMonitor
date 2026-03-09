#!/bin/bash

file="collected_file.txt"

nbLines=$(wc -l < "$file")

for((i=0; i < nbLines; i++)); do

    #Read the (i+1)th line
    line=$(sed -n "$((i+1))"p "$file")
    
    # Extract th title in 3rd column
    title=$(awk '{for(i=3; i<=NF; i++) printf $i " "; print ""}' <<< "$line")
done

# while IFS= read -r line; do
#     echo "LIne: $line"
# done < Opened_file.txt


    # for((j=0; j < nbLines; j++)); do
    #     var_line=$(sed -n "$((j+1))"p "$file")

    #     var_title=$(awk '{for(i=3; i<=NF; i++) printf $i " "; print ""}' <<< "$var_line")

    #     if [ "$title" -eq "$var_title" ]; then
            
    #     fi
    # done