(myenv) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization/Collect_info/Collect_command/command_desc$ python3 test3.py 
Enter command: echo "Hello World"

Element analysis:
  el_0: echo
  el_1: "Hello World"

=== FULL DESCRIPTION APPLIED ===

Descriptions found:
  desc_0: Print a text message. Note: Quotes are optional
  desc_1: Argument '"Hello World"'
(myenv) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization/Collect_info/Collect_command/command_desc$ python3 test3.py 
Enter command: ping 192.168.1.1

Element analysis:
  el_0: ping
  el_1: 192.168.1.1

=== FULL DESCRIPTION APPLIED ===

Descriptions found:
  desc_0: Ping the specified host
  desc_1: IP address '192.168.1.1'
(myenv) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization/Collect_info/Collect_command/command_desc$ python3 test3.py 
Enter command: curl http://example.com

Element analysis:
  el_0: curl
  el_1: http://example.com

=== FULL DESCRIPTION APPLIED ===

Descriptions found:
  desc_0: Make an HTTP GET request and dump the contents in `stdout`
  desc_1: URL 'http://example.com'
(myenv) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization/Collect_info/Collect_command/command_desc$ python3 test3.py 
Enter command: curl -d '{"name":"bob"}' -H "Content-Type: application/json"

Element analysis:
  el_0: curl
  el_1: curl -d
  el_2: '{"name":"bob"}'
  el_3: curl -H
  el_4: "Content-Type: application/json"

=== FULL DESCRIPTION APPLIED ===

Descriptions found:
  desc_0: Send data in JSON format, specifying the appropriate Content-Type header
  desc_1: Send data in JSON format, specifying the appropriate Content-Type header
  desc_2: JSON ''{"name":"bob"}''
  desc_3: Send data in JSON format, specifying the appropriate Content-Type header
  desc_4: Argument '"Content-Type: application/json"'
(myenv) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization/Collect_info/Collect_command/command_desc$ python3 test3.py 
Enter command: wget https://example.com/file.zip

Element analysis:
  el_0: wget
  el_1: https://example.com/file.zip

=== FULL DESCRIPTION APPLIED ===

Descriptions found:
  desc_0: Download the contents of a URL to a file (named "foo" in this case)
  desc_1: URL 'https://example.com/file.zip'
(myenv) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization/Collect_info/Collect_command/command_desc$ python3 test3.py 
Enter command: ssh user@192.168.1.10

Element analysis:
  el_0: ssh
  el_1: user@192.168.1.10

=== FULL DESCRIPTION APPLIED ===

Descriptions found:
  desc_0: Connect to a remote server
  desc_1: Argument 'user@192.168.1.10'
(myenv) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization/Collect_info/Collect_command/command_desc$ python3 test3.py 
Enter command: scp file.txt user@192.168.1.10:/tmp/

Element analysis:
  el_0: scp
  el_1: file.txt
  el_2: user@192.168.1.10:/tmp/

=== FULL DESCRIPTION APPLIED ===

Descriptions found:
  desc_0: Copy a local file to a remote host
  desc_1: File 'file.txt'
  desc_2: Argument 'user@192.168.1.10:/tmp/'



(myenv) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization/Collect_info/Collect_command/command_desc$ python3 test3.py 
Enter command: top -n 1

Element analysis:
  el_0: top
  el_1: top -n
  el_2: 1

=== FULL DESCRIPTION APPLIED ===

Descriptions found:
  desc_0: exit on maximum iterations NUMBER
  desc_1: exit on maximum iterations NUMBER
  desc_2: Port number '1'

(myenv) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization/Collect_info/Collect_command/command_desc$ python3 test3.py 
Enter command: ps aux | grep python

Element analysis:
  el_0: ps
  el_1: ps aux
  el_2: |
  el_3: grep
  el_4: python

=== FULL DESCRIPTION APPLIED ===

Descriptions found:
  desc_0: List all running processes
  desc_1: List all running processes
  desc_2: Argument '|'
  desc_3: File 'grep'
  desc_4: File 'python'

(myenv) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization/Collect_info/Collect_command/command_desc$ python3 test3.py 
Enter command: du -sh /home/user

Element analysis:
  el_0: du
  el_1: du -sh
  el_2: /home/user

=== FULL DESCRIPTION APPLIED ===

Descriptions found:
  desc_0: Show the size of a single directory, in human-readable units
  desc_1: Show the size of a single directory, in human-readable units
  desc_2: Folder '/home/user'


(myenv) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization/Collect_info/Collect_command/command_desc$ python3 test3.py 
Enter command: ls -l /tmp && echo "done"

Element analysis:
  el_0: ls
  el_1: ls -l
  el_2: /tmp
  el_3: &&
  el_4: echo
  el_5: "done"

=== FULL DESCRIPTION APPLIED ===

Descriptions found:
  desc_0: use a long listing format
  desc_1: use a long listing format
  desc_2: Folder '/tmp'
  desc_3: Argument '&&'
  desc_4: File 'echo'
  desc_5: File '"done"'


(myenv) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Visualization/Collect_info/Collect_command/command_desc$ python3 test3.py 
Enter command: cat file.txt | grep "hello" > output.txt

Element analysis:
  el_0: cat
  el_1: file.txt
  el_2: |
  el_3: grep
  el_4: "hello"
  el_5: >
  el_6: output.txt

=== FULL DESCRIPTION APPLIED ===

Descriptions found:
  desc_0: Print the contents of a file to `stdout`
  desc_1: File 'file.txt'
  desc_2: Argument '|'
  desc_3: File 'grep'
  desc_4: File '"hello"'
  desc_5: Argument '>'
  desc_6: File 'output.txt'


 
Enter command: cat file.txt | grep "hello" > output.txt

=== Command 1 ===
Element analysis:
  el_0: cat
  el_1: file.txt

=== FULL DESCRIPTION APPLIED ===
Descriptions found:
  desc_0: Print the contents of a file to `stdout`
  desc_1: File 'file.txt'

=== Command 2 ===
Element analysis:
  el_0: grep
  el_1: "hello"
  el_2: >
  el_3: output.txt

=== FULL DESCRIPTION APPLIED ===
Descriptions found:
  desc_0: Search for a pattern within a file
  desc_1: File '"hello"'
  desc_2: Argument '>'
  desc_3: File 'output.txt'
