# Raspberrypi の Wifi setting

androidの場合，これ使え！！！

```bash
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=JP

network={
	ssid="SSID(=スマホの名前)"
	psk="パスワード"
	proto=RSN
	priority=1
	id_str="mobile"
}
```

iphoneの場合，これ使え！！！

```bash
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=JP

network={
    ssid="iPhone"
    psk="pass"
    proto=RSN
    key_mgmt=WPA-PSK
    pairwise=CCMP
    auth_alg=OPEN
 }
```