#!/bin/bash
curl -sS -L --max-time 2400 -o /workspace/rom.tgz 'https://bkt-sgp-miui-ota-update-alisgp.oss-ap-southeast-1.aliyuncs.com/V14.0.4.0.TKSEUXM/camellian_eea_global_images_V14.0.4.0.TKSEUXM_20230914.0000.00_13.0_eea_af69a61f51.tgz'
echo $? > /workspace/rom.rc
