#!/usr/bin/env bash

MAP_DIR="carla_town05"
XODR_FILE="Town05.xodr"

mkdir -p $MAP_DIR
if [ ! -f $MAP_DIR/base_map.txt ]; then
    imap -f -i ./$XODR_FILE -o $MAP_DIR/base_map.txt
fi
rm -r $HOME/apollo/modules/map/data/$MAP_DIR
mv -f $MAP_DIR $HOME/apollo/modules/map/data/

DOCKER_USER="${USER}"
DEV_CONTAINER="apollo_dev_${USER}"
PATH=/usr/local/cuda/bin:/opt/apollo/neo/bin:/apollo/bazel-bin/modules/tools/visualizer:/apollo/bazel-bin/cyber/tools/cyber_launch:/apollo/bazel-bin/cyber/tools/cyber_service:/apollo/bazel-bin/cyber/tools/cyber_node:/apollo/bazel-bin/cyber/tools/cyber_channel:/apollo/bazel-bin/cyber/tools/cyber_monitor:/apollo/bazel-bin/cyber/tools/cyber_recorder:/apollo/bazel-bin/cyber/mainboard:/opt/apollo/sysroot/bin:/usr/local/nvidia/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/apollo/scripts:/usr/local/qt5/bin
PYTHONPATH=/apollo/bazel-bin/cyber/python/internal

xhost +local:root 1>/dev/null 2>&1

docker exec \
    -u "${DOCKER_USER}" \
    -e HISTFILE=/apollo/.dev_bash_hist \
    -e PATH="${PATH}" \
    -e PYTHONPATH="${PYTHONPATH}" \
    -it "${DEV_CONTAINER}" \
    /bin/bash -c "/apollo/bazel-bin/modules/map/tools/sim_map_generator -map_dir=/apollo/modules/map/data/${MAP_DIR} -output_dir=/apollo/modules/map/data/${MAP_DIR}"

docker exec \
    -u "${DOCKER_USER}" \
    -e HISTFILE=/apollo/.dev_bash_hist \
    -e PATH="${PATH}" \
    -e PYTHONPATH="${PYTHONPATH}" \
    -it "${DEV_CONTAINER}" \
    /bin/bash -c "/apollo/bazel-bin/modules/routing/topo_creator/topo_creator -map_dir=/apollo/modules/map/data/${MAP_DIR} --flagfile=/apollo/modules/routing/conf/routing.conf"

xhost -local:root 1>/dev/null 2>&1

cp -r $HOME/apollo/modules/map/data/$MAP_DIR ./
