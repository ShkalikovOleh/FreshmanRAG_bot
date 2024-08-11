#/env/bin/bash

mkdir -p data/db-data data/pgadmin-data data/es_data
sudo chown -R 1000:1000 data/es_data
sudo chown -R 5050:5050 data/pgadmin-data