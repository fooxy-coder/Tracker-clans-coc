#!/bin/bash
echo "=== ESTADO DUCKDNS ==="
echo "Última actualización:"
cat ~/duckdns/duck.log
echo ""
echo "IP actual externa:"
curl -s ifconfig.me
echo ""
