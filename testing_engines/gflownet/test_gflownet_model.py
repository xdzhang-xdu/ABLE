import os
import signal
from time import sleep

from testing_engines.gflownet.GFN_Fuzzing import covered_specs_7_31
from testing_engines.gflownet.generator.generative_model.main import generate_samples_with_gfn
from testing_engines.gflownet.generator.proxy.proxy_config import proxy_args
from testing_engines.gflownet.generator.proxy.train_proxy import train_proxy
from testing_engines.gflownet.path_config import path_args
import datetime
import subprocess
import docker
from multiprocessing import Process

def reboot_svl():
    if subprocess.call('cd ~/work/apollo;~/work/apollo/docker/scripts/dev_start.sh stop', shell=True):
        assert False, "Apollo container does not stop successfully."
    if subprocess.call('cd ~/work/apollo;./docker/scripts/dev_start.sh;./docker/scripts/dev_into.sh', shell=True):
        assert False, "Apollo container does not start successfully."
    client = docker.from_env()
    docker_ps_list = client.containers.list()
    docker_id = ""
    for container in docker_ps_list:
        if container.name == 'apollo_dev_xdzhang':
            docker_id = container.id
    if docker_id == "":
        assert False, "Apollo docker has not been starting well."
    cmd = "docker exec " + docker_id + " /bin/bash -c \"./scripts/bootstrap_lgsvl.sh\""
    if subprocess.call(cmd, shell=True):
        assert False, "Apollo docker has not been starting well."
    cmd = "docker exec " + docker_id + " /bin/bash -c \"./scripts/bridge.sh\""
    print("Apollo is beginning working...")
    if subprocess.call(cmd, stdout=subprocess.PIPE, shell=True):
        assert False, "Launching apollo-bridge is failed."


if __name__ == "__main__":
    # print(proxy_args)
    # train_proxy(proxy_args, "double_direction")
    # generate_samples_with_gfn("double_direction")
    # pid = Process(target=reboot_svl(), args=())
    # pid = Process(target=reboot_svl)
    # pid.start()
    # sleep(50)
    # pid.terminate()
    # if subprocess.call('cd ~/work/apollo;~/work/apollo/docker/scripts/dev_start.sh stop', shell=True):
    #     assert False, "Apollo container does not stop successfully."
    # pid = Process(target=reboot_svl)
    # pid.start()
    # sleep(2000)
    if "eventually((((signalAhead==0)and(junctionAhead<=1.0))and(Time>=20.0))and((always[0,3](not(highBeamOn==1)))and(always[0,3](not(lowBeamOn==1)))))" in  covered_specs_7_31:
        print("True")


