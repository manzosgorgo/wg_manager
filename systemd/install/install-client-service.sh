#!/bin/bash

cp /home/main/Desktop/wg_manager/systemd/wg-client-test@.service /home/main/Desktop/wg_manager/systemd/wg-client-test.socket   /etc/systemd/system
cp /home/main/Desktop/wg_manager/systemd/wg_client.conf /etc/tmpfiles.d/
systemd-tmpfiles --create /etc/tmpfiles.d/wg_client.conf
ls -ld /run/wg_manager
systemctl daemon-reload
systemctl reset-failed
systemctl cat wg-client-test@.service wg-client-test.socket --no-pager
systemctl restart wg-client-test.socket --no-pager
systemctl status wg-client-test@\*.service wg-client-test.socket --no-pager
