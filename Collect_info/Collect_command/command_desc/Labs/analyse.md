(myenv) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Vis/Collect_info/Collect_command/command_desc$ python3 test_program.py 
Enter command: curl -X GET "https://api.example.com/users" -H "Accept: application/json"

Element analysis:
  el_1: curl
  el_2: curl -X
  el_3: GET
  el_4: https://api.example.com/users
  el_5: curl -H
  el_6: Accept: application/json

Descriptions found:
  desc_1: Command 'curl'
  desc_2: Make an HTTP GET request and dump the contents in `stdout`
  desc_3: Argument GET
  desc_4: URL 'https://api.example.com/users'
  desc_5: Send a request with an extra header, using a custom HTTP method and over a proxy (such as BurpSuite), ignoring insecure self-signed certificates
  desc_6: Argument Accept: application/json

Enter command: curl -X POST "https://api.example.com/login" -d '{"user":"alice","pw":"x"}' -H "Content-Type: application/json"

Element analysis:
  el_1: curl
  el_2: curl -X
  el_3: POST
  el_4: https://api.example.com/login
  el_5: curl -d
  el_6: {"user":"alice","pw":"x"}
  el_7: curl -H
  el_8: Content-Type: application/json

Descriptions found:
  desc_1: Command 'curl'
  desc_2: Make an HTTP GET request and dump the contents in `stdout`
  desc_3: Argument POST
  desc_4: URL 'https://api.example.com/login'
  desc_5: Make an HTTP GET request, follow any `3xx` redirects, and dump the reply headers and contents to `stdout`
  desc_6: Argument {"user":"alice","pw":"x"}
  desc_7: Send a request with an extra header, using a custom HTTP method and over a proxy (such as BurpSuite), ignoring insecure self-signed certificates
  desc_8: Argument Content-Type: application/json

(myenv) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Vis/Collect_info/Collect_command/command_desc$ python3 test_program.py 
Enter command: http GET https://example.com/api/status

Element analysis:
  el_1: http
  el_2: GET
  el_3: https://example.com/api/status

Full command description:
  desc: Make a simple GET request (shows response headers and content)  (matched pattern: http https://example.com)

Descriptions found:
  desc_1: Make a simple GET request (shows response headers and content)
  desc_2: Argument GET
  desc_3: URL 'https://example.com/api/status'


(myenv) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Vis/Collect_info/Collect_command/command_desc$ python3 test_program.py 
Enter command: wget -q --show-progress https://example.com/archive.tar.gz

Element analysis:
  el_1: wget
  el_2: wget -q
  el_3: wget --show-progress
  el_4: https://example.com/archive.tar.gz

Descriptions found:
  desc_1: Command 'wget'
  desc_2: --quiet                     quiet (no output)
  desc_3: display the progress bar in any verbosity mode
  desc_4: URL 'https://example.com/archive.tar.gz'


(myenv) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Vis/Collect_info/Collect_command/command_desc$ python3 test_program.py 
Enter command: ls -la /var/log

Element analysis:
  el_1: ls
  el_2: ls -la
  el_3: /var/log

Descriptions found:
  desc_1: Command 'ls'
  desc_2: List files with a trailing symbol to indicate file type (directory/, symbolic_link@, executable*, ...)
  desc_3: Directory '/var/log'


(myenv) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Vis/Collect_info/Collect_command/command_desc$ python3 test_program.py 
Enter command: ls -l /home/user -a

Element analysis:
  el_1: ls
  el_2: ls -l
  el_3: /home/user
  el_4: ls -a

Descriptions found:
  desc_1: Command 'ls'
  desc_2: List all files in [l]ong format (permissions, ownership, size, and modification date)
  desc_3: Directory '/home/user'
  desc_4: List all files, including hidden files

(myenv) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Vis/Collect_info/Collect_command/command_desc$ python3 test_program.py 
Enter command: stat /etc/passwd

Element analysis:
  el_1: stat
  el_2: /etc/passwd

Full command description:
  desc: Display properties about a specific file such as size, permissions, creation and access dates among others  (matched pattern: stat path/to/file)

Descriptions found:
  desc_1: Display properties about a specific file such as size, permissions, creation and access dates among others
  desc_2: Directory '/etc/passwd'

(myenv) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Vis/Collect_info/Collect_command/command_desc$ python3 test_program.py 
Enter command: df -h

Element analysis:
  el_1: df
  el_2: df -h

Full command description:
  desc: print sizes in powers of 1024 (e.g., 1023M)  (matched pattern: df -h <arg>)

Descriptions found:
  desc_1: print sizes in powers of 1024 (e.g., 1023M)
  desc_2: print sizes in powers of 1024 (e.g., 1023M)

myenv) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Vis/Collect_info/Collect_command/command_desc$ python3 test_program.py 
Enter command: kill -9 12345

Element analysis:
  el_1: kill
  el_2: kill -9
  el_3: 12345

Full command description:
  desc: Signal the operating system to immediately terminate a program (which gets no chance to capture the signal)  (matched pattern: kill -9 process_id)

Descriptions found:
  desc_1: Signal the operating system to immediately terminate a program (which gets no chance to capture the signal)
  desc_2: Signal the operating system to immediately terminate a program (which gets no chance to capture the signal)
  desc_3: Port 12345

(myenv) aidan@aidan-Lenovo-N50-70:~/Documents/Projects/Vis/Collect_info/Collect_command/command_desc$ python3 test_program.py 
Enter command: ip addr show

Element analysis:
  el_1: ip
  el_2: addr
  el_3: show

Full command description:
  desc: Set the SSH version  (matched pattern: ip ssh version 2)

Descriptions found:
  desc_1: Set the SSH version
  desc_2: Argument addr
  desc_3: Argument show

