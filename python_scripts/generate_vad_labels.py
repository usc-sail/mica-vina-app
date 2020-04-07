###
###     Python Script to generate VAD labels given spliced-
###     log-Mel features as input
###
###     INPUTS:
###     write_dir    -  Directory in which to write all output files
###     scp_file     -  Kaldi feature file in .scp format
###     model_file   -  VAD model file trained on keras
###

###
###     OUTPUTS:
###     Frame-level posteriors from the model predictions
###     are thresholded at 0.5 and median-filtered with window length
###     of 550ms.
###    
###     write_post   -  Raw posteriors representing confidence in VAD prediction
###     write_ts     -  VAD segments detected written as start and end 
###                     end times.
###
###

from __future__ import division
import os, sys, numpy as np
np.warnings.filterwarnings('ignore')
os.environ["CUDA_VISIBLE_DEVICES"]=""
os.environ['TF_CPP_MIN_LOG_LEVEL']='3'
stderr = sys.stderr
sys.stderr = open(os.devnull, 'w')
import keras
sys.stderr = stderr
from keras.models import load_model
from scipy import signal as sig
from kaldi_io import read_mat_scp as rms
from keras import backend as K
import warnings
#warnings.filterwarnings("ignore")


##
##  Convert frame-level posteriors into 
##  continuous segments of regions where post=pos_label
##
def frame2seg(frames, frame_time_sec=0.01, pos_label=1):
    pos_idxs = np.where(frames==pos_label)[0]
    pos_regions = np.split(pos_idxs, np.where(np.diff(pos_idxs)!=1)[0]+1)
    if len(pos_idxs) == 0 or len(pos_regions) == 0:
        return []
    segments = np.array([[x[0], x[-1]+1] for x in pos_regions])*frame_time_sec
    return segments

def normalize(data):
    return np.divide(np.subtract(data, np.mean(data)), np.std(data))

#K.set_session(K.tf.Session(config=K.tf.ConfigProto(intra_op_parallelism_threads=8, inter_op_parallelism_threads=8)))
def generate_labels(write_dir, scp_file, model_file):
    frame_len = 0.01
    vad_wav_dir = os.path.join(write_dir, 'VAD/wavs') 
    write_post = os.path.join(write_dir, 'VAD/posteriors/')
    if not os.path.exists(write_post): os.makedirs(write_post)
    write_ts   = os.path.join(write_dir, 'VAD/timestamps/')
    if not os.path.exists(write_ts): os.makedirs(write_ts)
    
    model = load_model(model_file)
    gen = rms(scp_file)

    # Generate VAD posteriors using pre-trained VAD model
    for key, mat in gen:
        predictions = []
        movie = key
    #    fts = normalize(mat)
        fts = mat
        num_seg = int(len(fts)//64)
        for i in range(num_seg):
            feats_seg = normalize(fts[i*64:(i+1)*64])
            pred = model.predict(feats_seg.reshape((1, 64, 64, 1)), verbose=0)
    #        pred = [x[1] for x in pred]
            predictions.append(pred[0][1])
    #movie = keybz.split('_seg')[0]

        # Post-processing of posteriors
        labels = np.array([np.repeat(x, 64) for x in predictions]).flatten()
        seg_times = frame2seg(np.round(labels))
    #    print(labels)
     #   print(seg_times)
        # Write start and end VAD timestamps 
        fw = open(os.path.join(write_ts, movie + '_wo_ss.ts'),'w')
        if not os.path.exists(os.path.join(vad_wav_dir,movie)):
            os.makedirs(os.path.join(vad_wav_dir, movie))

        seg_ct = 1
        for segment in seg_times:
            if segment[1]-segment[0] > 0.05:
                fw.write('{0}_vad-{1:04}\t{0}\t{2:0.2f}\t{3:0.2f}\n'.format(movie, seg_ct, segment[0], segment[1]))
                ## 16kHz audio segments required to perform speaker homogenous segmentation
     #           cmd = 'sox -V1 {0}.wav -r 16k {1}/{2}_vad-{3:04}.wav trim {4} ={5}'.format(os.path.join(write_dir,'wavs',movie), os.path.join(vad_wav_dir, movie), movie, seg_ct, segment[0], segment[1])
      #          os.system(cmd)
                seg_ct += 1
        fw.close()

        # Write frame-level posterior probabilities
        fpost = open(os.path.join(write_post, movie + '.post'),'w')
        for frame in predictions:
            fpost.write('{0:0.2f}\n'.format(frame))
        fpost.close()

        fw.close()

if __name__ == '__main__':
    write_dir, scp_file, model_file = sys.argv[1:]
    generate_labels(write_dir, scp_file, model_file)
