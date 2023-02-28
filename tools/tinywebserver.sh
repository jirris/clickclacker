#!/bin/bash
# Run for example in screen or as service. Access with webrowser and port 8000 e.g. http://127.0.0.1:8000
while :; do { echo -ne "HTTP/1.0 200 OK\r\nContent-Length: $(wc -c <~/clickclack/data/schedule.html)\r\n\r\n"; cat ~/clickclack/data/schedule.html; } | nc -l -p 8000; done