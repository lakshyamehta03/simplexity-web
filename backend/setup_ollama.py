#!/usr/bin/env python3
"""
Setup script for Ollama LLM classifier
This script helps install and configure Ollama for the Ripplica AI project
"""

import subprocess
import sys
import os
import platform
import requests
import time
from pathlib import Path

def check_ollama_installed():
    """Check if Ollama is already installed"""
    try:
        result = subprocess.run(['ollama', '--version'], 
                              capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

def install_ollama():
    """Install Ollama based on the operating system"""
    system = platform.system().lower()
    
    print("Installing Ollama...")
    
    if system == "windows":
        print("For Windows, please install Ollama manually:")
        print("1. Visit: https://ollama.ai/download")
        print("2. Download the Windows installer")
        print("3. Run the installer and follow the instructions")
        print("4. Restart your terminal after installation")
        return False
        
    elif system == "darwin":  # macOS
        try:
            subprocess.run(['curl', '-fsSL', 'https://ollama.ai/install.sh'], 
                         shell=True, check=True)
            print("Ollama installed successfully on macOS")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to install Ollama on macOS: {e}")
            return False
            
    elif system == "linux":
        try:
            subprocess.run(['curl', '-fsSL', 'https://ollama.ai/install.sh'], 
                         shell=True, check=True)
            print("Ollama installed successfully on Linux")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to install Ollama on Linux: {e}")
            return False
    else:
        print(f"Unsupported operating system: {system}")
        return False

def start_ollama_service():
    """Start the Ollama service"""
    print("Starting Ollama service...")
    
    try:
        # Check if Ollama is already running
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("Ollama service is already running")
            return True
    except requests.exceptions.RequestException:
        pass
    
    try:
        # Start Ollama in the background
        if platform.system().lower() == "windows":
            subprocess.Popen(['ollama', 'serve'], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
        else:
            subprocess.Popen(['ollama', 'serve'], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL,
                           start_new_session=True)
        
        # Wait for service to start
        print("Waiting for Ollama service to start...")
        for i in range(30):  # Wait up to 30 seconds
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=5)
                if response.status_code == 200:
                    print("Ollama service started successfully")
                    return True
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)
        
        print("Failed to start Ollama service")
        return False
        
    except Exception as e:
        print(f"Error starting Ollama service: {e}")
        return False

def download_model(model_name="llama2"):
    """Download a specific Ollama model"""
    print(f"Downloading {model_name} model...")
    
    try:
        # Check if model is already downloaded
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get("models", [])
            if any(model["name"] == model_name for model in models):
                print(f"{model_name} model is already downloaded")
                return True
        
        # Download the model
        subprocess.run(['ollama', 'pull', model_name], check=True)
        print(f"{model_name} model downloaded successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Failed to download {model_name} model: {e}")
        return False
    except Exception as e:
        print(f"Error downloading model: {e}")
        return False

def test_classifier():
    """Test the LLM classifier"""
    print("Testing the LLM classifier...")
    
    try:
        from llm_classifier import LLMClassifier
        
        classifier = LLMClassifier(model_name="llama2")
        
        # Test with a simple query
        test_query = "What is machine learning?"
        result = classifier.classify_query(test_query)
        
        print(f"Test query: {test_query}")
        print(f"Classification result: {result}")
        print("Classifier test successful!")
        return True
        
    except Exception as e:
        print(f"Classifier test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("Ripplica AI - Ollama Setup")
    print("=" * 40)
    
    # Check if Ollama is installed
    if not check_ollama_installed():
        print("Ollama is not installed.")
        if not install_ollama():
            print("Please install Ollama manually and run this script again.")
            return False
    else:
        print("Ollama is already installed")
    
    # Start Ollama service
    if not start_ollama_service():
        print("Failed to start Ollama service")
        return False
    
    # Download default model
    if not download_model("llama2"):
        print("Failed to download llama2 model")
        return False
    
    # Test the classifier
    if not test_classifier():
        print("Failed to test classifier")
        return False
    
    print("\n" + "=" * 40)
    print("Setup completed successfully!")
    print("You can now use the LLM classifier in your Ripplica AI project.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 