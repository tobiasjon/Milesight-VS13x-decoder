#!/bin/bash

echo "=== .env Generator ==="

read -p "MQTT Host [prod.iotjonkopingslan.se]: " mqtt_host
mqtt_host=${mqtt_host:-prod.iotjonkopingslan.se}

read -p "MQTT Port [8883]: " mqtt_port
mqtt_port=${mqtt_port:-8883}

read -p "MQTT Username: " mqtt_username
read -s -p "MQTT Password: " mqtt_password
echo

read -p "Client ID: " client_id
read -p "Installation ID: " installation_id

read -p "Base URL [https://lynx-jkpg.iotopen.se]: " baseurl
baseurl=${baseurl:-https://lynx-jkpg.iotopen.se}

cat <<EOF > .env
IOTOPEN_MQTT_HOST=$mqtt_host
IOTOPEN_MQTT_PORT=$mqtt_port
IOTOPEN_MQTT_USERNAME=$mqtt_username
IOTOPEN_MQTT_PASSWORD=$mqtt_password
IOTOPEN_CLIENT_ID=$client_id
IOTOPEN_INSTALLATION_ID=$installation_id
IOTOPEN_BASEURL=$baseurl
EOF

echo "✅ .env file created!"