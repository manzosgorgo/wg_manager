#!/bin/bash

cp /home/main/Desktop/wg_manager/systemd/wg-controller-test@.service /home/main/Desktop/wg_manager/systemd/wg-controller-test.socket  /etc/systemd/system
systemctl daemon-reload
systemctl reset-failed
systemctl cat wg-controller-test@.service wg-controller-test.socket --no-pager
systemctl status wg-controller-test@\*.service wg-controller-test.socket --no-pager