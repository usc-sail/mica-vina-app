##
##      
##      Perform speaker-homogenous segmentation of audio
##

expt_dir=${1}
wav_dir=${2}
scpfile=${3}
log_ss=${4}

mkdir -p $expt_dir/VAD/spk_seg
ls $wav_dir/*.wav > $expt_dir/wav.list
fc=1
for wav_file in `cat $expt_dir/wav.list`
do
    file_name=`basename $wav_file .wav`
    extract-segments scp:$scpfile $expt_dir/VAD/timestamps/${file_name}_wo_ss.ts ark:- 2>>$log_ss | \
     compute-mfcc-feats ark:- ark:- 2>>$log_ss | \
        spk-seg --bic-alpha=1.1 ark:- $expt_dir/VAD/spk_seg/${file_name}.seg 2>>$log_ss
done
