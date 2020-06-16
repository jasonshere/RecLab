import math
import sys

import numpy as np

sys.path.append('../')
sys.path.append('../../')
from env_defaults import *
from run_utils import get_env_dataset, run_env_experiment
from run_utils import ModelTuner
from reclab.environments import LatentFactorBehavior
from reclab.recommenders import LibFM

# ====Step 4====
# S3 storage parameters
bucket_name = 'recsys-eval'
data_dir = 'master'
overwrite = True

# Experiment setup.
n_trials = 10
len_trial = get_len_trial(LATENT_STATIC)
trial_seeds = [i for i in range(n_trials)]

# Environment setup
environment_name = LATENT_STATIC['name']
env = LatentFactorBehavior(**LATENT_STATIC['params'], **LATENT_STATIC['optional_params'])

# Recommender setup
recommender_name = 'LibFM (SGD)'
recommender_class = LibFM


# ====Step 5====
starting_data = get_env_dataset(env)


# ====Step 6====
# Recommender tuning setup
n_fold = 5
num_users, num_items = get_num_users_items(LATENT_STATIC)
default_params = dict(num_user_features=0,
                      num_item_features=0,
                      num_rating_features=0,
                      max_num_users=num_users,
                      max_num_items=num_items,
                      method='sgd')
tuner = ModelTuner(starting_data,
                   default_params,
                   recommender_class,
                   n_fold=n_fold,
                   verbose=True,
                   bucket_name=bucket_name,
                   data_dir=data_dir,
                   environment_name=environment_name,
                   recommender_name=recommender_name,
                   overwrite=overwrite)

# Verify that the performance dependent hyperparameters lead to increased performance.
print("Larger latent dimensions should lead to increased performance.")
init_stdevs = [1.0]
num_iters = [1000]
num_two_ways = np.linspace(1, 100, 10, dtype=np.int).tolist()
tuner.evaluate_grid(num_two_way_factors=num_two_ways,
                    num_iter=num_iters,
                    init_stdev=init_stdevs)

# Set latent dimension to tradeoff runtime and performance.
num_two_way_factors = 20

print("More iterations should lead to increased performance.")
init_stdevs = [1.0]
num_iters = np.linspace(1, 1000, 10, dtype=np.int).tolist()
num_two_ways = [num_two_way_factors]
tuner.evaluate_grid(num_two_way_factors=num_two_ways,
                    num_iter=num_iters,
                    init_stdev=init_stdevs)

# Set number of iterations to tradeoff runtime and performance.
num_iter = 200

# Tune the performance independent hyperparameters.
init_stdevs = [1.0]
regs = np.linspace(0.01, 0.1, 10).tolist()
lrs = np.linspace(1e-3, 1e-2, 5).tolist()
num_iters = [num_iter]
num_two_ways = [num_two_way_factors]
results = tuner.evaluate_grid(num_two_way_factors=num_two_ways,
                    num_iter=num_iters,
                    init_stdev=init_stdevs,
                    reg=regs,
                    learning_rate=lrs
                    )

# Set parameters based on tuning
init_stdev = 1.0
best_params = results[results['average_metric'] == results['average_metric'].min()]
reg = float(best_params['reg'])
lr = float(best_params['learning_rate'])

# ====Step 7====
recommender = recommender_class(num_iter=num_iter,
                                num_two_way_factors=num_two_way_factors,
                                init_stdev=init_stdev,
                                reg=reg,
                                learning_rate=lr,
                                **default_params)
for i, seed in enumerate(trial_seeds):
    run_env_experiment(
            [env],
            [recommender],
            [seed],
            len_trial,
            environment_names=[environment_name],
            recommender_names=[recommender_name],
            bucket_name=bucket_name,
            data_dir=data_dir,
            overwrite=overwrite)
