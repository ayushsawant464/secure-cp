#!/bin/bash
#
# Quick Browser Test - Just launches kiosk mode browser
#

echo "Opening browser in kiosk mode..."
echo "Press Alt+F4 to close when done"
echo ""

# Clean up old profile
rm -rf /tmp/exam-browser-test

# Launch browser
google-chrome \
  --kiosk https://codeforces.com \
  --no-first-run \
  --disable-session-crashed-bubble \
  --disable-infobars \
  --disable-dev-tools \
  --disable-extensions \
  --user-data-dir=/tmp/exam-browser-test \
  --no-default-browser-check \
  2>/dev/null

echo "Browser closed"
