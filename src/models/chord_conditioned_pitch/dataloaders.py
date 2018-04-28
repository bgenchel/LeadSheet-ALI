import numpy as np
import pdb
from torch.utils.data import DataLoader

TARGET_PITCH_VECTOR_SIZE = 128
TARGET_DUR_VECTOR_SIZE = 18

class LeadSheetDataLoader(DataLoader):
    """
    DataLoader class for lead sheet data parsed from music xml.
    """

    def __init__(self, dataset, num_songs=None, **kwargs):
        super(LeadSheetDataLoader, self).__init__(**kwargs)
        """
        Initializes the class, defines the number of batches and other parameters
        Args:
                dataset:  	object of the RawAudioDataset class, should be properly initialized
                num_data_pts:	int, number of data points to be considered while loading the data
        """
        train, valid = dataset['train'], dataset['valid']
        if num_songs is None:
            num_songs = len(train)
        # check if input parameters are accurate
        assert num_songs <= len(train)
        self.train = train[:num_songs]
        self.valid = valid
        self.num_songs = num_songs

    def _get_seqs(self, seq_key="", seq_len=2, target_as_vector=False, target_vector_size=-1):
        train_seqs = []
        train_targets = []
        valid_seqs = []
        valid_targets = []
        for song in self.train:
            song_seq = []
            for measure in song['measures']:
                for i, thing in enumerate(measure[seq_key]):
                    song_seq.append(thing)

            for i in range(0, len(song_seq) - seq_len):
                train_seqs.append(np.array(song_seq[i:i+seq_len]))

                if target_as_vector:
                    target = np.zeros(target_vector_size)
                    target[song_seq[i + seq_len]] = 1
                    train_targets.append(target)
                else:
                    train_targets.append(song_seq[i+seq_len])
                
        for song in self.valid:
            song_seq = []
            for measure in song['measures']:
                for i, thing in enumerate(measure[seq_key]):
                    song_seq.append(thing)

            for i in range(0, len(song_seq) - seq_len):
                valid_seqs.append(np.array(song_seq[i:i+seq_len]))

                if target_as_vector:
                    target = np.zeros(target_vector_size)
                    target[song_seq[i + seq_len]] = 1
                    valid_targets.append(target)
                else:
                    valid_targets.append(song_seq[i+seq_len])

        return (np.array(train_seqs), np.array(train_targets),
                np.array(valid_seqs), np.array(valid_targets))

    def _get_batched(self, seqs_getter, seq_len=2, batch_size=1, target_as_vector=False):
        (train_seqs, train_targets, 
         valid_seqs, valid_targets) = seqs_getter(seq_len=seq_len, target_as_vector=target_as_vector)
        assert batch_size <= len(train_seqs)
        assert batch_size <= len(valid_seqs)
        num_train_batches = int(np.floor(len(train_seqs) / batch_size))
        num_valid_batches = int(np.floor(len(valid_seqs) / batch_size))
        batched_train_seqs = np.split(
                train_seqs[:num_train_batches*batch_size], num_train_batches, axis=0)
        batched_train_targets = np.split(
                train_targets[:num_train_batches*batch_size], num_train_batches, axis=0)
        batched_valid_seqs = np.split(
                valid_seqs[:num_valid_batches*batch_size], num_valid_batches, axis=0)
        batched_valid_targets = np.split(
                valid_targets[:num_valid_batches*batch_size], num_valid_batches, axis=0)
        return (np.array(batched_train_seqs), np.array(batched_train_targets),
                np.array(batched_valid_seqs), np.array(batched_valid_targets))

    def get_harmony(self, seq_len=2):
        train_seqs = []
        train_targets = []
        valid_seqs = []
        valid_targets = []
        for song in self.train:
            song_pitch_harmonies = []
            for measure in song['measures']:
                harmony_index = 0
                for i in range(len(measure['pitch_numbers'])):
                    if (i == measure['half_index']) and (len(measure['harmonies']) > 1):
                        harmony_index += 1
                    song_pitch_harmonies.append(measure['harmonies'][harmony_index])

            for i in range(0, len(song_pitch_harmonies) - seq_len):
                train_seqs.append(np.array(song_pitch_harmonies[i:i+seq_len]))
                train_targets.append(np.array(song_pitch_harmonies[i+seq_len]))

        for song in self.valid:
            song_pitch_harmonies = []
            for measure in song['measures']:
                harmony_index = 0
                for i, pitch in enumerate(measure['pitch_numbers']):
                    if (i == measure['half_index']) and (len(measure['harmonies']) > 1):
                        harmony_index += 1
                    song_pitch_harmonies.append(measure['harmonies'][harmony_index])

            for i in range(0, len(song_pitch_harmonies) - seq_len):
                valid_seqs.append(np.array(song_pitch_harmonies[i:i+seq_len]))
                valid_targets.append(np.array(song_pitch_harmonies[i+seq_len]))

        return (np.array(train_seqs), np.array(train_targets),
                np.array(valid_seqs), np.array(valid_targets))


    def get_batched_harmony(self, seq_len=2, batch_size=1):
        (batched_train_seqs, batched_train_targets,
         batched_valid_seqs, batched_valid_targets) = self._get_batched(self.get_harmony, seq_len, batch_size)
        return (np.array(batched_train_seqs), np.array(batched_train_targets),
                np.array(batched_valid_seqs), np.array(batched_valid_targets))

    def get_pitch_seqs(self, seq_len=2, target_as_vector=False):
        train_seqs, train_targets, valid_seqs, valid_targets = self._get_seqs(
                "pitch_numbers", seq_len, target_as_vector, TARGET_PITCH_VECTOR_SIZE)
        return (train_seqs, train_targets, valid_seqs, valid_targets)

    def get_batched_pitch_seqs(self, seq_len=2, batch_size=1, target_as_vector=False):
        (batched_train_seqs, batched_train_targets,
         batched_valid_seqs, batched_valid_targets) = self._get_batched(
                self.get_pitch_seqs, seq_len, batch_size, target_as_vector)
        return (batched_train_seqs, batched_train_targets, 
                batched_valid_seqs, batched_valid_targets)

    def get_dur_seqs(self, seq_len=2, target_as_vector=False):
        train_seqs, train_targets, valid_seqs, valid_targets = self._get_seqs(
                "duration_tags", seq_len, target_as_vector, TARGET_DUR_VECTOR_SIZE)
        return (train_seqs, train_targets, valid_seqs, valid_targets)

    def get_batched_dur_seqs(self, seq_len=2, batch_size=1, target_as_vector=False):
        (batched_train_seqs, batched_train_targets,
         batched_valid_seqs, batched_valid_targets) = self._get_batched(
                self.get_dur_seqs, seq_len, batch_size, target_as_vector)
        return (batched_train_seqs, batched_train_targets, 
                batched_valid_seqs, batched_valid_targets)
