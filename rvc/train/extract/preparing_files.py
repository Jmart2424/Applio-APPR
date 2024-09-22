import os
import shutil
from random import shuffle
from rvc.configs.config import Config
import re

config = Config()
current_directory = os.getcwd()


def generate_config(rvc_version: str, sample_rate: int, model_path: str):
    config_path = os.path.join("rvc", "configs", rvc_version, f"{sample_rate}.json")
    config_save_path = os.path.join(model_path, "config.json")
    if not os.path.exists(config_save_path):
        shutil.copyfile(config_path, config_save_path)


def generate_filelist(
    pitch_guidance: bool, model_path: str, rvc_version: str, sample_rate: int
):
    gt_wavs_dir = os.path.join(model_path, "sliced_audios")
    feature_dir = os.path.join(model_path, f"{rvc_version}_extracted")

    f0_dir, f0nsf_dir = None, None
    if pitch_guidance:
        f0_dir = os.path.join(model_path, "f0")
        f0nsf_dir = os.path.join(model_path, "f0_voiced")

    gt_wavs_files = set(name.split(".")[0] for name in os.listdir(gt_wavs_dir))
    feature_files = set(name.split(".")[0] for name in os.listdir(feature_dir))

    if pitch_guidance:
        f0_files = set(name.split(".")[0] for name in os.listdir(f0_dir))
        f0nsf_files = set(name.split(".")[0] for name in os.listdir(f0nsf_dir))
        names = gt_wavs_files & feature_files & f0_files & f0nsf_files
    else:
        names = gt_wavs_files & feature_files

    options = []
    mute_base_path = os.path.join(current_directory, "logs", "mute")

    sid_pattern = re.compile(r'^(\d+)_')

    for name in names:
        sid_match = sid_pattern.match(name)
        sid = sid_match.group(1) if sid_match else None

        if pitch_guidance:
            options.append(
                f"{gt_wavs_dir}/{name}.wav|{feature_dir}/{name}.npy|{f0_dir}/{name}.wav.npy|{f0nsf_dir}/{name}.wav.npy|{sid}"
            )
        else:
            options.append(f"{gt_wavs_dir}/{name}.wav|{feature_dir}/{name}.npy|{sid}")

    mute_audio_path = os.path.join(
        mute_base_path, "sliced_audios", f"mute{sample_rate}.wav"
    )
    mute_feature_path = os.path.join(
        mute_base_path, f"{rvc_version}_extracted", "mute.npy"
    )

    for _ in range(2):
        if pitch_guidance:
            mute_f0_path = os.path.join(mute_base_path, "f0", "mute.wav.npy")
            mute_f0nsf_path = os.path.join(mute_base_path, "f0_voiced", "mute.wav.npy")
            options.append(
                f"{mute_audio_path}|{mute_feature_path}|{mute_f0_path}|{mute_f0nsf_path}|0"
            )
        else:
            options.append(f"{mute_audio_path}|{mute_feature_path}|0")

    shuffle(options)

    with open(os.path.join(model_path, "filelist.txt"), "w") as f:
        f.write("\n".join(options))
