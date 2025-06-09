#!/usr/bin/env python
"""
Heroku deployment helper script for Cabinet Medicale backend.
This script helps with setting up environment variables on Heroku.
"""
import os
import sys
import subprocess
import argparse

def check_heroku_cli():
    """Check if Heroku CLI is installed."""
    try:
        subprocess.run(['heroku', '--version'], check=True, stdout=subprocess.PIPE)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

def check_heroku_login():
    """Check if user is logged in to Heroku."""
    try:
        result = subprocess.run(['heroku', 'auth:whoami'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.SubprocessError:
        return False

def create_heroku_app(app_name):
    """Create a new Heroku app."""
    try:
        subprocess.run(['heroku', 'create', app_name], check=True)
        print(f"✅ Created Heroku app: {app_name}")
        return True
    except subprocess.SubprocessError as e:
        print(f"❌ Failed to create Heroku app: {e}")
        return False

def set_heroku_env_vars(app_name, env_file='.env'):
    """Set environment variables on Heroku from .env file."""
    if not os.path.exists(env_file):
        print(f"❌ Environment file {env_file} not found")
        return False
    
    # Read environment variables from .env file
    env_vars = {}
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            key, value = line.split('=', 1)
            env_vars[key] = value
    
    # Set environment variables on Heroku
    for key, value in env_vars.items():
        try:
            subprocess.run(['heroku', 'config:set', f"{key}={value}", '--app', app_name], check=True)
        except subprocess.SubprocessError as e:
            print(f"❌ Failed to set environment variable {key}: {e}")
            return False
    
    # Set additional Heroku-specific variables
    subprocess.run(['heroku', 'config:set', 'IS_HEROKU=True', '--app', app_name], check=True)
    subprocess.run(['heroku', 'config:set', 'ENVIRONMENT=production', '--app', app_name], check=True)
    
    print(f"✅ Environment variables set on Heroku app: {app_name}")
    return True

def add_postgres_addon(app_name):
    """Add PostgreSQL addon to Heroku app."""
    try:
        subprocess.run(['heroku', 'addons:create', 'heroku-postgresql:hobby-dev', '--app', app_name], check=True)
        print(f"✅ Added PostgreSQL addon to Heroku app: {app_name}")
        return True
    except subprocess.SubprocessError as e:
        print(f"❌ Failed to add PostgreSQL addon: {e}")
        return False

def deploy_to_heroku(app_name):
    """Deploy the application to Heroku."""
    try:
        # Check if git is initialized
        if not os.path.exists('.git'):
            subprocess.run(['git', 'init'], check=True)
            subprocess.run(['git', 'add', '.'], check=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit for Heroku deployment'], check=True)
        
        # Add Heroku remote
        subprocess.run(['heroku', 'git:remote', '-a', app_name], check=True)
        
        # Push to Heroku
        subprocess.run(['git', 'push', 'heroku', 'master'], check=True)
        print(f"✅ Deployed to Heroku app: {app_name}")
        
        # Run migrations
        subprocess.run(['heroku', 'run', 'python', 'manage.py', 'migrate', '--app', app_name], check=True)
        print(f"✅ Ran migrations on Heroku app: {app_name}")
        
        return True
    except subprocess.SubprocessError as e:
        print(f"❌ Failed to deploy to Heroku: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Deploy Cabinet Medicale backend to Heroku')
    parser.add_argument('app_name', help='Name of the Heroku app')
    parser.add_argument('--env-file', default='.env', help='Path to .env file (default: .env)')
    parser.add_argument('--create', action='store_true', help='Create a new Heroku app')
    parser.add_argument('--set-env', action='store_true', help='Set environment variables on Heroku')
    parser.add_argument('--add-postgres', action='store_true', help='Add PostgreSQL addon to Heroku app')
    parser.add_argument('--deploy', action='store_true', help='Deploy to Heroku')
    parser.add_argument('--all', action='store_true', help='Perform all actions')
    
    args = parser.parse_args()
    
    # Check if Heroku CLI is installed
    if not check_heroku_cli():
        print("❌ Heroku CLI is not installed. Please install it first.")
        return 1
    
    # Check if user is logged in to Heroku
    if not check_heroku_login():
        print("❌ You are not logged in to Heroku. Please run 'heroku login' first.")
        return 1
    
    # Perform actions based on arguments
    if args.create or args.all:
        if not create_heroku_app(args.app_name):
            return 1
    
    if args.add_postgres or args.all:
        if not add_postgres_addon(args.app_name):
            return 1
    
    if args.set_env or args.all:
        if not set_heroku_env_vars(args.app_name, args.env_file):
            return 1
    
    if args.deploy or args.all:
        if not deploy_to_heroku(args.app_name):
            return 1
    
    print(f"✅ Done! Your app is available at: https://{args.app_name}.herokuapp.com/")
    return 0

if __name__ == '__main__':
    sys.exit(main())
