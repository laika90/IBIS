expect -c "
  set timeout 3
  spawn ssh pi@raspberrypi.local
  expect \"password:\"
  send \"ibis\n\"
  interact
"
