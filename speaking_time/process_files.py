from __future__ import division
import sys, os, numpy as np
from flask import Flask
from flask import current_app
from rq import get_current_job
from speaking_time.config import *
from speaking_time.email import send_email
import glob
import shutil
sys.path.insert(0, os.path.join(SCRIPT_DIR, 'python_scripts'))
sys.path.insert(0, os.path.join(SCRIPT_DIR, 'python_scripts/audioset_scripts'))
from generate_vad_labels import *
from predict_gender import *
from spk_seg_to_vad_ts import convert_seg_file
from download_vggish_ckpt_file import download_ckpt
import vggish_input, vggish_params, vggish_postprocess, vggish_slim
from compute_and_write_vggish_feats import compute_vggish_embeddings
from gender_resegmentation import cluster_segments

def compute_total_speech_time(vad_dir):
    try:
        ts_file = glob.glob(os.path.join(vad_dir, 'timestamps', '*wo_ss.ts'))[0]
        ts_data = [x.rstrip().split() for x in open(ts_file, 'r').readlines()]
        ts_segs = [[float(x[2]), float(x[3])] for x in ts_data]
        time = np.sum(np.diff(ts_segs))
        hh = int(time / 3600)
        mm = int(time / 60) - 60*hh
        ss = (time - 3600*hh - 60*mm)
        return '{hh:02}:{mm:02}:{ss:.2f}'.format(hh=hh, mm=mm, ss=ss)
    except: 
        return '-'

#OUT_DIR='/Users/rabbeh/Projects/ITU/flask_proj/mod_proj/app/out_dir'
def run_pipeline(data_filepath, emailID):
    job = get_current_job()
#    gender = {'male':'M', 'female':'F'}
    if emailID != "":
        MAIL_RECIPIENTS=[emailID]
    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)
    #if not os.path.isdir(LOG_DIR):
    #    os.makedirs(LOG_DIR)

    log_file = os.path.join(OUT_DIR, 'itu_speaking_time.log')
#    if mod_gender not in gender.keys():
#        print("Invalid option for gender")
#        exit()

    filename = data_filepath.rsplit('/')[-1].split('.')[0]
    job.meta['file_id'] = filename
    job.save_meta()
    out_dir = os.path.join(OUT_DIR, filename)
    attempt = 1
    while os.path.exists(out_dir):
        out_dir = out_dir.split('_rerun')[0] + '_rerun{}'.format(attempt)
        attempt += 1
    #    shutil.rmtree(out_dir)
    os.makedirs(out_dir)
    paths_file = os.path.join(out_dir, 'file_list.txt')
        
    fw = open(paths_file, 'w')
    fw.write('{}\n'.format(data_filepath))#, gender[mod_gender], mod_start, mod_end))
    fw.close()
    
    ## Create all directories and paths
    dirs = {}
    dirs['wav_16k'] = os.path.join(out_dir, 'wavs_16k')
    dirs['feats'] = os.path.join(out_dir, 'features')
    dirs['vad'] = os.path.join(out_dir, 'VAD')
    dirs['gender'] = os.path.join(os.path.join(out_dir, 'GENDER'), filename)
    log_ss = os.path.join(dirs['feats'], 'speaker_segmentation.log')
    vad_model = os.path.join(SCRIPT_DIR, 'models/vad.h5')
    gender_model = os.path.join(SCRIPT_DIR, 'models/gender.h5')
    pca_params = os.path.join(SCRIPT_DIR, 'python_scripts/audioset_scripts/vggish_pca_params.npz')
    checkpoint = os.path.join(SCRIPT_DIR, 'python_scripts/audioset_scripts/vggish_model.ckpt')

    for direc in dirs.values():
        os.makedirs(direc)
    dirs['vggish'] = os.path.join(dirs['feats'], 'vggish')
    os.makedirs(dirs['vggish'])

    
    ## Create wav files
    print(" >>>> CREATING WAV FILES <<<< ")
    job.meta['prog'] = 'Extracting audio (1/6)'
    job.save_meta()
    os.system('bash {}/bash_scripts/create_wav_files.sh {} {} 16000 1'.format(SCRIPT_DIR, paths_file, dirs['wav_16k']))

    
    ## Create logmel feats
    print(" >>>> EXTRACTING LOGMEL FEATURES <<<< ")
    job.meta['prog'] = 'Computing features for speech detection (2/6)'
    job.save_meta()
    os.system('bash {}/bash_scripts/create_logmel_feats.sh {} {} 1'.format(SCRIPT_DIR, dirs['wav_16k'], dirs['feats']))

    ## Generate VAD labels; NOTE: not optimized for multiple-files, please see speaking_time_non_controlled.sh
    print(" >>>> GENERATING VAD LABELS <<<< ")
    job.meta['prog'] = 'Detecting speech regions (3/6)'
    job.save_meta()
    generate_labels(out_dir, os.path.join(dirs['feats'], 'feats.scp'), vad_model)
    job.meta['tot_spc'] = compute_total_speech_time(dirs['vad'])
    job.save_meta()

    ## Speaker segmentation
    print(" >>>> SPEAKER SEGMENTATION <<<< ")
    job.meta['prog'] = 'Speaker segmentation (4/6)'
    job.save_meta()
    os.system('bash {}/bash_scripts/do_spk_seg.sh {} {} {} {}'.format(SCRIPT_DIR, out_dir, dirs['wav_16k'], os.path.join(dirs['feats'], 'wav.scp'), log_ss))
    convert_seg_file(filename, out_dir)
    
    ## Extract vggish-embeddings
    print(" >>>> VGGISH EMBEDDINGS <<<< ")
    job.meta['prog'] = 'Computing features for gender ID (5/6)'
    job.save_meta()
    wav_file = glob.glob(os.path.join(dirs['wav_16k'], '*.wav'))[0]
    compute_vggish_embeddings(SCRIPT_DIR, wav_file, pca_params, checkpoint, dirs['vggish'])

    ## Predict Gender
    print(" >>>> PREDICTING GENDER SEGMENTS <<<< ")
    job.meta['prog'] = 'Determining gender for speech segments (6/6)'
    job.save_meta()
    compute_gender_predictions(out_dir, gender_model)
    cluster_segments(dirs['gender'])
    
    
    spk_time_data = [x.rstrip().split() for x in open(os.path.join(dirs['gender'], filename + '.ts'), 'r').readlines()]
    male_time = sum([float(x[1])-float(x[0]) for x in spk_time_data if x[2]=='male'])
    female_time = sum([float(x[1])-float(x[0]) for x in spk_time_data if x[2]=='female'])
    
    job.meta['per_fem'] = round(female_time/(male_time + female_time)*100, 2)
    job.meta['prog'] = 'Done inference'
    job.save_meta()
    
    
    #os.system('bash {}/speaking_time_non_controlled.sh {} {}'.format(SCRIPT_DIR, paths_file, out_dir))
    msg = 'Hi\nFile {} has been processed. PFA speaking time estimates attached\nThis is an automated email, please do not reply to this email-address. To provide feedback, you can contact the author at rajatheb@usc.edu'.format(filename)
    csv_file = os.path.join(out_dir, 'GENDER/{0}/{0}.csv'.format(filename))
    if not os.path.isfile(csv_file):
        csv_file = glob.glob(os.path.join(out_dir, 'GENDER/*/*.csv'))[0]

    with open(csv_file, 'r') as fp:
        csv_att = [csv_file.split('/')[-1], "text/plain", fp.read()]

    atts = [csv_att]

    with open(log_file, 'a') as logf:
        logf.write('{}\t{}\t{}\t{}\n'.format(emailID, filename, out_dir, job.meta['prog']))
    if emailID != '':
        send_email(subject = MAIL_SUBJECT, sender = MAIL_USERNAME, recipients = MAIL_RECIPIENTS, text_body=msg, html_body='', attachments=atts, sync=True)

if __name__=='__main__':
    data_path = sys.argv[1]
    run_pipeline(data_path)
