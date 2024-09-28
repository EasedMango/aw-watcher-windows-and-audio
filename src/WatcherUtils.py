import tomllib
import os
import sys

def get_config(file_name : str):
    try:
        # Determine base directory depending on whether the script is frozen (.exe) or not
        if getattr(sys, 'frozen', False):  # This checks if running as a compiled .exe
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Build the config file path
        config_file = os.path.join(base_dir, file_name+".toml")
        
        # Check if the config file exists, create if not
        if not os.path.isfile(config_file):
            with open(config_file, 'w') as f:
                f.write("""
[settings]
# run for testing server
testing = false  
# heartbeat/update rate
sleep-time = 0.5 
# event merge time
pulse-time = 2.0 
""")
        
        # Try to load the configuration file
        with open(config_file, "rb") as f:
            return tomllib.load(f)

    except (OSError, tomllib.TOMLDecodeError) as e:
        # Handle file system errors or TOML parsing errors and exit the program
        print(f"Error: Failed to load config file. Details: {e}")
        raise SystemExit(1)  # Exit with status code 1 indicating an error