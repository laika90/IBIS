expect -c "
  set timeout 3
  spawn ssh hum-bird@hum-bird
  expect \"password:\"
  send \"raspberry\n\"
  interact
"
