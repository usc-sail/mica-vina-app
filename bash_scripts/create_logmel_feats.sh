#!/bin/bash
## 
##
##  Extract spliced log-Mel filterbank energy features
##
##  Arguments :
##
##      wav_dir     - Directory in which sampled .wav files are 
##                      stored
##      feats_dir   - Directory in which to store all features
##      nj          - Number of parallel jobs to run
##

wav_dir=$1
feats_dir=$2
nj=$3

log_dir=$feats_dir/log
fbank_dir=$feats_dir/fbank_data
scp=$feats_dir/wav.scp

mkdir -p $log_dir $fbank_dir #$spl_dir

if [ -f path.sh ];  then ./path.sh; fi 


find $wav_dir -type f -name '*.wav' | while read r
do
    movie_name=`basename $r .wav`
    echo $movie_name" "$r
done > $scp

sort $scp -o $scp
#sort $segments -o $segments

####
####    Extract log-Mel filterbank coefficients
####

## Split wav.scp into 'nj' parts
split_wav_scp=""
for n in $(seq $nj); do
    split_wav_scp="$split_wav_scp $log_dir/wav.scp.$n"
done
utils/split_scp.pl $scp $split_wav_scp || exit 1;

## Extract fbank features using run.pl parallelization
utils/run.pl JOB=1:$nj $log_dir/make_fbank_feats.JOB.log \
    compute-fbank-feats --verbose=2 --num-mel-bins=64 scp:$log_dir/wav.scp.JOB ark,p:- \| \
    copy-feats --compress=true ark,p:- \
        ark,scp,p:$fbank_dir/raw_fbank_feats.JOB.ark,$fbank_dir/raw_fbank_feats.JOB.scp \
# || exit 1;

## Combine multiple fbank files and delete segment split files
#rm $log_dir/segments* 2>/dev/null 
for n in $(seq $nj); do
  cat $fbank_dir/raw_fbank_feats.$n.scp || exit 1;
done > $feats_dir/feats.scp
