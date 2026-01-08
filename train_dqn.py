# train_dqn.py
import argparse, os
from stable_baselines3 import DQN
from stable_baselines3.common.callbacks import CheckpointCallback
from sumo_env_dqn import SumoDQNEnv

def main(args):
    if args.seed is not None:
        import numpy as np
        np.random.seed(args.seed)
    env = SumoDQNEnv(args.sumo_config, max_steps=args.episode_length, min_green=args.min_green)
    if args.load_model:
        model = DQN.load(args.load_model, env=env)
        print(f'Loaded model from {args.load_model}')
    else:
        model = DQN('MlpPolicy', env, verbose=1, buffer_size=50000, learning_rate=5e-4, batch_size=64, gamma=0.95, exploration_fraction=0.014, target_update_interval=500, policy_kwargs={'net_arch': [64, 64]}, seed=args.seed)
    os.makedirs('models', exist_ok=True)
    checkpoint = CheckpointCallback(save_freq=5000, save_path='models/', name_prefix=f'dqn_sumo_seed{args.seed}')
    model.learn(total_timesteps=args.timesteps, callback=checkpoint, reset_num_timesteps=False)
    model.save(f'{args.save_model}_seed{args.seed}')
    print('Saved model to', f'{args.save_model}_seed{args.seed}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--sumo-config', required=True)
    parser.add_argument('--timesteps', type=int, default=720000)
    parser.add_argument('--save-model', default='dqn_sumo_model')
    parser.add_argument('--load-model', help='Path to load a pre-trained model')
    parser.add_argument('--episode-length', type=int, default=3600)
    parser.add_argument('--min-green', type=int, default=5)
    parser.add_argument('--seed', type=int, help='Random seed for reproducibility')
    args = parser.parse_args()
    main(args)
