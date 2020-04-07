##
##  Author/year : Rajat Hebbar/2018
##
##  Extract audio (mono, sampled at 8/16 kHz) from given AV files
##
##  Input:
##      1) AV_paths : text file, with each line having complete path to a single AV file
##      2) wav_dir     : directory in which to store complete audio files
##      3) frate       : rate at which to sample audio (Hz)
##      4) nj          : number of parallel jobs to process
##
##  Output:
##      1) Raw audio file in ".wav" format for each file in AV_paths
##



AV_paths=${1}
wav_dir=${2}
frate=${3}
nj=${4}


file_num=1
for AV_file in `awk '{print $1}' $AV_paths`
do
    base=`basename -- $AV_file`
    file_name=`echo $base | awk -F '.' '{ print $1 }'` 

    ffmpeg -loglevel error -i $AV_file -ar $frate -ac 1 $wav_dir/$file_name.wav &  ## Extract single-channel audio from input sampled at $frate Hz.
    if [ $(($file_num % $nj )) -eq 0 ]
    then
        wait
    fi
    file_num=`expr $file_num + 1`
done
wait
