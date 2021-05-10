import glob

import numpy as np
import pandas as pd
from tqdm import tqdm

FILE_TYPE_DIR_PLACEHOLDER = "<file_type_dir>"
FILE_EXT_PLACEHOLDER = "<file_ext>"

def get_speakers(file_path):
    df = pd.read_csv(file_path, sep="\s+", index_col=False)
    return list(df["ID"])

def get_all_data(dir_path, txt_subdir="txt", audio_subdir="wav48"):
    speakers_ls = get_speakers(f"{dir_path}/speaker-info.txt")
    file_output = []
    with tqdm(speakers_ls) as speakers:
        for speaker_id in speakers:
            speaker_dir_path = f"{dir_path}/<file_type_dir>/p{speaker_id}"

            audio_dir = speaker_dir_path.replace(FILE_TYPE_DIR_PLACEHOLDER, audio_subdir)
            speaker_mel_ls = sorted(glob.glob(f"{audio_dir}/*.mel.npy"))
            
            txt_dir = speaker_dir_path.replace(FILE_TYPE_DIR_PLACEHOLDER, txt_subdir)
            speaker_phones_ls = sorted(glob.glob(f"{txt_dir}/*.phones"))

            if len(speaker_mel_ls) != len(speaker_phones_ls):
                print(f"skipping speaker {speaker_id} because the no. of mel files ({len(speaker_mel_ls)}) and phones files ({len(speaker_phones_ls)}) should be the same")
                continue

            for i in range(len(speaker_mel_ls)):
                row = []
                filename = speaker_phones_ls[i].split("/")[-1].split(".")[0]

                assert filename == speaker_mel_ls[i].split("/")[-1].split(".")[0]

                row.append(f"{speaker_dir_path}/{filename}.{FILE_EXT_PLACEHOLDER}")

                row.append(str(np.load(speaker_mel_ls[i]).shape[0]))
                with open(speaker_phones_ls[i]) as s_phone_file:
                    phones_ls = s_phone_file.read().split()
                    row.append(str(len(phones_ls)))

                # row_str = ",".join(row)
                file_output.append(row)

    all_data_df = pd.DataFrame(data=file_output, columns=["path", "n_frames", "n_phones"])

    return all_data_df

def split_data(all_data_df):
    msk = np.random.rand(len(all_data_df)) < 0.8

    train_df = all_data_df[msk]
    val_df = all_data_df[~msk]

    return train_df, val_df

if __name__ == "__main__":
    dataset_dir_path = "/home/headquarters/Desktop/masters/nonparaSeq2seqVC_code/dataset/DS_10283_2651/VCTK-Corpus"
    np.random.seed(420)

    print(f"getting all data from {dataset_dir_path}...")
    all_data_df = get_all_data(dataset_dir_path)
    print(f"splitting data...")
    train_df, val_df = split_data(all_data_df)

    print(f"writing data to files...")
    all_data_df.to_csv(f"{dataset_dir_path}/all_data.csv")
    train_df.to_csv(f"{dataset_dir_path}/train.csv")
    val_df.to_csv(f"{dataset_dir_path}/val.csv")
