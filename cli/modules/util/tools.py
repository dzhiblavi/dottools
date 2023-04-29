import subprocess
import yaml


def has_gpu():
    try:
        subprocess.check_call(
            args=['nvidia-smi'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=True,
        )
        return True

    except subprocess.SubprocessError:
        return False


def load_yaml_by_path(path):
    with open(path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)
