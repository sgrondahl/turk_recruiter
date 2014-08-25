
#### To give user-mode access to port 80:

 iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8080

### Goals

Simplify panel recruiting and management, with a focus on recruiting
from Amazon's Mechanical Turk.