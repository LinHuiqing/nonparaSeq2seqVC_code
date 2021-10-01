from pydub import AudioSegment
import glob, os
from tqdm import tqdm
import argparse

# def get_speakers(file_path):
#     df = pd.read_csv(file_path, sep="\s+", index_col=False)
#     return list(df["ID"])

MIN_FRAME_LEN, MAX_FRAME_LEN = 160, 9000

def _detect_leading_silence(sound, silence_threshold=20.0, chunk_size=1, relative=True):
    '''
    sound is a pydub.AudioSegment
    silence_threshold in dB
    chunk_size in ms

    iterate over chunks until you find the first one with sound
    '''
    trim_ms = 0 # ms
    if relative:
        dBFS = sound.dBFS
    else:
        dBFS = 0

    assert chunk_size > 0 # to avoid infinite loop
    while sound[trim_ms:trim_ms+chunk_size].dBFS < dBFS-silence_threshold and trim_ms < len(sound):
        trim_ms += chunk_size
    return trim_ms

def trim_silence(sound, silence_threshold=20.0, chunk_size=1, relative=True):
    start_trim = _detect_leading_silence(sound, 
                                         silence_threshold=silence_threshold, 
                                         chunk_size=chunk_size, 
                                         relative=relative)
    end_trim = _detect_leading_silence(sound.reverse(), 
                                       silence_threshold=silence_threshold, 
                                       chunk_size=chunk_size, 
                                       relative=relative)

    duration = len(sound)
    return sound[start_trim:duration-end_trim]

def get_files_with_ext(wav_dir, ext):
    wav_files = []
    os.chdir(wav_dir)
    for file in glob.glob(f"*/*.{ext}"):
        wav_files.append(f"{wav_dir}/{file}")
    return wav_files

def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trim silences from start and end of audio files.")
    parser.add_argument("--path", required=True, help="Directory path of directory with audio recordings from root.")
    parser.add_argument("--threshold", required=False, type=int, default=20, help="Silence threshold to trim for.")
    parser.add_argument("--relative", type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Activate relative mode.")
    args = parser.parse_args()

    # dir_path = "dataset/DS_10283_2651/VCTK-Corpus"
    # speakers_ls = get_speakers(f"{dir_path}/speaker-info.txt")
    wav_files = get_files_with_ext(args.path, "wav")

    with tqdm(wav_files) as wav_files:
        for i, wav_file_path in enumerate(wav_files):
            sound = AudioSegment.from_file(wav_file_path, format="wav")
            trimmed_sound = trim_silence(sound, 
                                         silence_threshold=args.threshold, 
                                         relative=args.relative)
            if MIN_FRAME_LEN <= len(trimmed_sound) <= MAX_FRAME_LEN:
                trimmed_sound.export(wav_file_path, format="wav")
            else:
                print(f"removing {wav_file_path} has it has len {len(trimmed_sound)} which exceeds the limits of {MIN_FRAME_LEN} and {MAX_FRAME_LEN}")
