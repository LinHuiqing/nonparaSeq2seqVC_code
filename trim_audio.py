from pydub import AudioSegment
import glob, os
from tqdm import tqdm
# import pandas as pd

# def get_speakers(file_path):
#     df = pd.read_csv(file_path, sep="\s+", index_col=False)
#     return list(df["ID"])

def _detect_leading_silence(sound, silence_threshold=-30.0, chunk_size=1):
    '''
    sound is a pydub.AudioSegment
    silence_threshold in dB
    chunk_size in ms

    iterate over chunks until you find the first one with sound
    '''
    trim_ms = 0 # ms

    assert chunk_size > 0 # to avoid infinite loop
    while sound[trim_ms:trim_ms+chunk_size].dBFS < silence_threshold and trim_ms < len(sound):
        trim_ms += chunk_size

    return trim_ms

def trim_silence(sound, silence_threshold=-30.0, chunk_size=1):
    start_trim = _detect_leading_silence(sound, silence_threshold, chunk_size)
    end_trim = _detect_leading_silence(sound.reverse(), silence_threshold, chunk_size)

    duration = len(sound)
    return sound[start_trim:duration-end_trim]

def get_files_with_ext(wav_dir, ext):
    # for file in os.listdir(wav_dir):
    #     if file.endswith(ext):
    #         print(os.path.join(wav_dir, file))
    wav_files = []
    os.chdir(wav_dir)
    for file in glob.glob(f"*/*.{ext}"):
        wav_files.append(f"{wav_dir}/{file}")
    return wav_files

if __name__ == "__main__":
    # dir_path = "dataset/DS_10283_2651/VCTK-Corpus"
    # speakers_ls = get_speakers(f"{dir_path}/speaker-info.txt")
    # /home/headquarters/Desktop/masters/nonparaSeq2seqVC_code/dataset/DS_10283_2651/VCTK-Corpus/wav48/p273
    wav_files = get_files_with_ext("/home/headquarters/Desktop/masters/nonparaSeq2seqVC_code/dataset/VCTK-Corpus/wav48", "wav")

    with tqdm(wav_files) as wav_files:
        for wav_file_path in wav_files:
            sound = AudioSegment.from_file(wav_file_path, format="wav")
            trimmed_sound = trim_silence(sound)
            if len(trimmed_sound) >= 345:
                trimmed_sound.export(wav_file_path, format="wav")
            else:
                print(f"removing {wav_file_path} has it has len {len(trimmed_sound)} < 345")
                os.remove(wav_file_path)
