# milesight mqtt decoder for vs133 and vs135 sensors

This is Milesight decoder/reformater for vs133 and vs135 Milesight sensors connected with ethernet.
The sensors need to be configured to send the data to IoT-Open with MQTT protocol. 
This decoder will transform incomming MQTT data from the sensors and create Functions and Devices for each sensor as well as resending the data the the topic_read names.

Today it supports only Linecross counting. I will add child counter as well as zones in comming versions.

## Installation
First create a Installation in IoT-Open that will have the Milesight sensors and note the client_ID and installation_ID.
Also prepare a API account and key.

Pull down the repo to a machine that has docker installed
There is a generate_env.sh script that can help you fill create the .env file for your installation.

When you filled the .env file you can start the decoder by running
''' 
docker-compose up -d --build
'''

Depending on when the Milesight device sends an update that is when the device gets created in IoT-Open.




