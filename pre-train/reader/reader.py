import torch
import torch.utils.data
import random
import numpy as np
from .symbols import ph2id, sp2id
from torch.utils.data import DataLoader
import pandas as pd

FILE_TYPE_DIR_PLACEHOLDER = "<file_type_dir>"
FILE_EXT_PLACEHOLDER = "<file_ext>"
TEXT_SUBDIR = "txt"
AUDIO_SUBDIR = "wav48"
MEL_EXT = "mel.npy"
SPEC_EXT = "spec.npy"
PHONES_EXT = "phones"

def read_text(fn):
    '''
    read phone alignments from file of the format:
    start end phone
    '''
    with open(fn) as f:
        file_contents = f.read()
    phones = file_contents.strip().split()
    return phones

class TextMelIDLoader(torch.utils.data.Dataset):
    
    def __init__(self, list_file, mean_std_file, shuffle=True):
        '''
        list_file: 3-column: (path, n_frames, n_phones)
        mean_std_file: tensor loadable into numpy, of shape (2, feat_dims), i.e. [mean_row, std_row]
        '''
        df = pd.read_csv(list_file)
        file_path_list = list(df["path"])

        if shuffle:
            random.seed(420)
            random.shuffle(file_path_list)
        
        self.file_path_list = file_path_list
        self.mel_mean_std = np.float32(np.load(mean_std_file))
        self.spc_mean_std = np.float32(np.load(mean_std_file.replace('mel', 'spec')))

    def get_path_id(self, path):
        # Custom this function to obtain paths and speaker id
        # Deduce filenames
        spec_path = path
        text_path = path.replace(AUDIO_SUBDIR, TEXT_SUBDIR).replace(SPEC_EXT, PHONES_EXT)
        mel_path = path.replace(SPEC_EXT, MEL_EXT)
        speaker_id = path.split('/')[-2].lstrip('p')

        return mel_path, spec_path, text_path, speaker_id


    def get_text_mel_id_pair(self, path):
        '''
        You should Modify this function to read your own data.

        Returns:

        object: dimensionality
        -----------------------
        text_input: [len_text]
        mel: [mel_bin, len_mel]
        mel: [spc_bin, len_spc]
        speaker_id: [1]
        '''

        mel_path, spec_path, text_path, speaker_id = self.get_path_id(path)
        # Load data from disk
        text_input = self.get_text(text_path)
        mel = np.load(mel_path)
        spc = np.load(spec_path)
        # Normalize audio 
        mel = (mel - self.mel_mean_std[0])/ self.mel_mean_std[1]
        spc = (spc - self.spc_mean_std[0]) / self.spc_mean_std[1]
        # Format for pytorch
        text_input = torch.LongTensor(text_input)
        mel = torch.from_numpy(np.transpose(mel))
        spc = torch.from_numpy(np.transpose(spc))
        speaker_id = torch.LongTensor([sp2id[speaker_id]])

        return (text_input, mel, spc, speaker_id)
        
    def get_text(self,text_path):
        '''
        Returns:

        text_input: a list of phoneme IDs corresponding 
        to the transcript of one utterance
        '''
        text = read_text(text_path)
        text_input = []

        for ph in text:
            text_input.append(ph2id[ph])
        
        return text_input

    def __getitem__(self, index):
        '''
        Returns:
        
        
        '''
        generic_file_path = self.file_path_list[index]
        spec_file_path = generic_file_path.replace(FILE_TYPE_DIR_PLACEHOLDER, AUDIO_SUBDIR)
        spec_file_path = spec_file_path.replace(FILE_EXT_PLACEHOLDER, SPEC_EXT)
        return self.get_text_mel_id_pair(spec_file_path)

    def __len__(self):
        return len(self.file_path_list)


class TextMelIDCollate():

    def __init__(self, n_frames_per_step=2):
        self.n_frames_per_step = n_frames_per_step

    def __call__(self, batch):
        '''
        batch is list of (text_input, mel, spc, speaker_id)
        '''
        text_lengths = torch.IntTensor([len(x[0]) for x in batch])
        mel_lengths = torch.IntTensor([x[1].size(1) for x in batch])
        mel_bin = batch[0][1].size(0)
        spc_bin = batch[0][2].size(0)

        max_text_len = torch.max(text_lengths).item()
        max_mel_len = torch.max(mel_lengths).item()
        if max_mel_len % self.n_frames_per_step != 0:
            max_mel_len += self.n_frames_per_step - max_mel_len % self.n_frames_per_step
            assert max_mel_len % self.n_frames_per_step == 0

        text_input_padded = torch.LongTensor(len(batch), max_text_len)
        mel_padded = torch.FloatTensor(len(batch), mel_bin, max_mel_len)
        spc_padded = torch.FloatTensor(len(batch), spc_bin, max_mel_len)

        speaker_id = torch.LongTensor(len(batch))
        stop_token_padded = torch.FloatTensor(len(batch), max_mel_len)

        text_input_padded.zero_()
        mel_padded.zero_()
        spc_padded.zero_()
        speaker_id.zero_()
        stop_token_padded.zero_()

        for i in range(len(batch)):
            text =  batch[i][0]
            mel = batch[i][1]
            spc = batch[i][2]

            text_input_padded[i,:text.size(0)] = text 
            mel_padded[i,  :, :mel.size(1)] = mel
            spc_padded[i,  :, :spc.size(1)] = spc
            speaker_id[i] = batch[i][3][0]
            # make sure the downsampled stop_token_padded have the last eng flag 1. 
            stop_token_padded[i, mel.size(1)-self.n_frames_per_step:] = 1

        return text_input_padded, mel_padded, spc_padded, speaker_id, \
                    text_lengths, mel_lengths, stop_token_padded
    
