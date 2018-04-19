#!/bin/bash

source /www/api.pingpawn.com/.venv/bin/activate
exec uwsgi --enable-threads --ini /www/api.pingpawn.com/pingpawn_api.ini --gid www-data 

