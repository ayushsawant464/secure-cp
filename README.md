# secure-cp

A proof of concept (POC) vibe coded and tested in testing mode.
DO NOT TEST OR USE IN PRODUCTION MODE.
Main idea was to make a secure vpn tunnel and allow traffic only to allow-listed domains through the tunnel.
All network calls are only to be made through vpn BlOCK every other call. 
Monitor running processes before and during exam
and block all processes or calls except those present in allowlist.
Prevent tampering of application.

## Future scope

- Test rigorously especially kernel code.
- Add chrome safety features for example user should not be able to escape
kiosk mode, prevent other tools access.
- VM based cheating is not  detected.
- Estimate scalability of solution by testing at scale.
