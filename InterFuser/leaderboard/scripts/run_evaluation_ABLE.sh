#!/bin/bash

export CARLA_ROOT=carla
export CARLA_SERVER=${CARLA_ROOT}/CarlaUE4.sh
export PYTHONPATH=$PYTHONPATH:${CARLA_ROOT}/PythonAPI
export PYTHONPATH=$PYTHONPATH:${CARLA_ROOT}/PythonAPI/carla
export PYTHONPATH=$PYTHONPATH:$CARLA_ROOT/PythonAPI/carla/dist/carla-0.9.13-py3.7-linux-x86_64.egg
export PYTHONPATH=$PYTHONPATH:leaderboard
export PYTHONPATH=$PYTHONPATH:leaderboard/team_code
export PYTHONPATH=$PYTHONPATH:scenario_runner_able_edition

export LEADERBOARD_ROOT=leaderboard
export CHALLENGE_TRACK_CODENAME=SENSORS
export PORT=2000 # same as the carla server port
export TM_PORT=2500 # port for traffic manager, required when spawning multiple servers/clients
export DEBUG_CHALLENGE=0
export ROUTES=able.xml
export TEAM_AGENT=leaderboard/team_code/interfuser_agent.py # agent
export TEAM_CONFIG=leaderboard/team_code/interfuser_config.py # model checkpoint, not required for expert
export ABLE=$1 #scenario_runner_able_edition/trace/trace_test.json
export SAVE_PATH=data/eval # path for saving episodes while evaluating

if [ "${ABLE}" = "" ]; then
    export ABLE="scenario_runner_able_edition/trace/trace_test.json"
    echo "Default ABLE file trace_test.json is used."
else
    echo "ABLE file "${ABLE}" is used."
fi

python3 ${LEADERBOARD_ROOT}/leaderboard/leaderboard_evaluator_ABLE.py \
--able=${ABLE} \
--track=${CHALLENGE_TRACK_CODENAME} \
--agent=${TEAM_AGENT} \
--agent-config=${TEAM_CONFIG} \
--debug=${DEBUG_CHALLENGE} \
--port=${PORT} \
--trafficManagerPort=${TM_PORT}
