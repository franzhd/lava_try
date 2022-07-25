#!/bin/bash
export NNI_PLATFORM='local'
export NNI_EXP_ID='u25wldfa'
export NNI_SYS_DIR='/home/franzhd/lava_try/dataset_encoding/nni-experiments/u25wldfa/trials/E3Coh'
export NNI_TRIAL_JOB_ID='E3Coh'
export NNI_OUTPUT_DIR='/home/franzhd/lava_try/dataset_encoding/nni-experiments/u25wldfa/trials/E3Coh'
export NNI_TRIAL_SEQ_ID='2'
export NNI_CODE_DIR='/home/franzhd/lava_try/dataset_encoding'
cd $NNI_CODE_DIR
eval python3 Dataset_encoding.py 1>/home/franzhd/lava_try/dataset_encoding/nni-experiments/u25wldfa/trials/E3Coh/stdout 2>/home/franzhd/lava_try/dataset_encoding/nni-experiments/u25wldfa/trials/E3Coh/stderr
echo $? `date +%s%3N` >'/home/franzhd/lava_try/dataset_encoding/nni-experiments/u25wldfa/trials/E3Coh/.nni/state'