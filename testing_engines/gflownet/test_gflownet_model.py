from testing_engines.gflownet.generator.generative_model.main import generate_samples_with_gfn
from testing_engines.gflownet.generator.proxy.proxy_config import proxy_args
from testing_engines.gflownet.generator.proxy.train_proxy import train_proxy
from testing_engines.gflownet.path_config import path_args

if __name__ == "__main__":
    # print(proxy_args)
    train_proxy(proxy_args, "double_direction")
    generate_samples_with_gfn("double_direction")
