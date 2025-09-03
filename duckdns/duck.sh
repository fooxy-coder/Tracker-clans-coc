#!/bin/bash
echo url="https://www.duckdns.org/update?domains=mitracker&token=e062ebac-b604-4de2-a7da-5b209b524c5f&ip=" | curl -k -o ~/duckdns/duck.log -K -
