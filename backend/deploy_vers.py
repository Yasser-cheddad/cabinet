#!/usr/bin/env python
"""
Deploy React + Vite frontend to Vercel from the command line.
Make sure Vercel CLI is installed and you're logged in.
"""

import os
import sys
import subprocess
import argparse

def check_vercel_cli():
    """Check if Vercel CLI is installed."""
    try:
        subprocess.run(['vercel', '--version'], check=True, stdout=subprocess.PIPE)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

def check_vercel_login():
    """Check if user is logged in to Vercel."""
    try:
        result = subprocess.run(['vercel', 'whoami'], check=True, stdout=subprocess.PIPE)
        user = result.stdout.decode().strip()
        print(f"✅ Logged in as: {user}")
        return True
    except subprocess.SubprocessError:
        return False

def set_env_vars(project_dir, env_file):
    """Set environment variables on Vercel using CLI."""
    if not os.path.exists(env_file):
        print(f"❌ Environment file {env_file} not found.")
        return False

    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            key, value = line.split('=', 1)
            try:
                subprocess.run(['vercel', 'env', 'add', key, 'production'], cwd=project_dir, input=value.encode(), check=True)
                print(f"✅ Set {key} for production")
            except subprocess.SubprocessError:
                print(f"⚠️ Failed to set environment variable {key}")
    
    return True

def deploy_frontend(project_dir, prod=True):
    """Deploy the frontend using Vercel CLI."""
    try:
        command = ['vercel', '--prod'] if prod else ['vercel']
        subprocess.run(command, cwd=project_dir, check=True)
        print("✅ Frontend deployed successfully.")
        return True
    except subprocess.SubprocessError as e:
        print(f"❌ Deployment failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Deploy React + Vite frontend to Vercel")
    parser.add_argument('--path', default='frontend', help='Path to frontend folder (default: frontend)')
    parser.add_argument('--env-file', default='.env', help='Path to .env file')
    parser.add_argument('--set-env', action='store_true', help='Set environment variables on Vercel')
    parser.add_argument('--deploy', action='store_true', help='Deploy the app')
    parser.add_argument('--all', action='store_true', help='Run all steps (set-env + deploy)')
    
    args = parser.parse_args()
    frontend_path = os.path.abspath(args.path)

    if not check_vercel_cli():
        print("❌ Vercel CLI not installed. Run: npm install -g vercel")
        return 1

    if not check_vercel_login():
        print("❌ Not logged in to Vercel. Run: vercel login")
        return 1

    if args.set_env or args.all:
        if not set_env_vars(frontend_path, args.env_file):
            return 1

    if args.deploy or args.all:
        if not deploy_frontend(frontend_path):
            return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())
