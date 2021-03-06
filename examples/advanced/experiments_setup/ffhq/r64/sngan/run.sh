#!/usr/bin/env bash

# logdir with ALL of the experiments
MAINLOGDIR=logs/experiments
# experiment id (relative path in main logdir)
EXPERIMENT_ID=ffhq/r64/sngan_grid_search

LOGDIR="$MAINLOGDIR/$EXPERIMENT_ID"
OUTDIR="examples/advanced/rendered/$EXPERIMENT_ID"

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

#python catalyst_gan/rendering.py -t \
#    examples/advanced/tconfigs/config_base.yml \
#    examples/advanced/tconfigs/eval/inception/fid.yml \
#    examples/advanced/tconfigs/data/FFHQ.yml \
#    examples/advanced/tconfigs/tloss.yml \
#    examples/advanced/tconfigs/model/r64/dcgan.yml \
#    examples/advanced/tconfigs/optim/tstatic_choise.yml \
#    -n base eval data loss model optim \
#    -p "$DIR/params.yml" \
#    --out_dir $OUTDIR \
#    --exp_dir $LOGDIR

# check similar to dcgan
sh $DIR/gan/run.sh
sh $DIR/wgan/run.sh
sh $DIR/wgan_gp/run.sh
sh $DIR/hinge/run.sh

#./$OUTDIR/run_command_check.txt
#./$OUTDIR/run_command.txt