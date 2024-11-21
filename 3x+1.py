import os
import time
import sys
import logging
import datetime as d

# Constants
init = 295000000000000000000000
TIMEOUT_LIMIT = 5 * 60  # 5 minutes

# File paths
SAVE_FILE = '3x+1.save'
BACKUP_FILE = '3x+1.backup.save'
TIMEOUT_FILE = '3x+1.timeout'
LOG_FILE = '3x+1.log'


# Set up logging to file only (no terminal output)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',  # With timestamp and log level
    handlers=[
        logging.FileHandler(LOG_FILE)  # Log only to a file, no console output
    ]
)

# Cross-platform file lock
def lock_file(file):
    if sys.platform == 'win32':  # Windows-specific
        import msvcrt
        msvcrt.locking(file.fileno(), msvcrt.LK_LOCK, 0)  # Lock the entire file (nbytes = 0)
    else:  # Unix-like platforms (Linux, macOS)
        import fcntl
        fcntl.flock(file, fcntl.LOCK_EX)


def unlock_file(file):
    # Windows-specific file unlock logic (skip unlocking on Windows)
    if sys.platform == 'win32':
        pass  # No explicit unlock needed on Windows
    else:  # Unix-like platforms (Linux, macOS)
        try:
            import fcntl
            fcntl.flock(file, fcntl.LOCK_UN)
        except IOError:
            logging.error("IOError while unlocking file on Unix-like system.")


# Main processing function
def main_process(init_seed, seed):
    logging.info("Starting the main process.")

    try:
        with open(SAVE_FILE, 'r+') as file:  # Open file in read/write mode
            lock_file(file)
            try:
                seed = int(file.read())  # Read saved seed
                logging.info(f"Seed read from main save file: {seed}")
            except ValueError:
                logging.warning("ERROR: Invalid value in main save file.")
                pass
            finally:
                unlock_file(file)

        if seed == init_seed:  # Fallback logic if the file is invalid
            try:
                with open(BACKUP_FILE, 'r+') as file:
                    lock_file(file)
                    try:
                        seed = int(file.read())  # Read backup seed
                        logging.info(f"Seed read from backup save file: {seed}")
                    except ValueError:
                        logging.warning("ERROR: Invalid value in backup save file.")
                        pass
                    finally:
                        unlock_file(file)
            except FileNotFoundError:
                logging.error("ERROR: No valid seed found. Starting with initial seed.")
                seed = init_seed

    except FileNotFoundError:
        logging.error("ERROR: No save files found. Starting with initial seed.")
        seed = init_seed

    # Main logic
    if seed % 2 == 0:
        seed += 1  # Ensure the seed starts as an odd number
        logging.info(f"Seed adjusted to odd: {seed}")

    # Iterative Collatz sequence
    while True:
        seed += 2  # Increment by 2 to stay odd

        x = seed
        while True:
            if x % 2 == 0 and x >= seed:
                x = x // 2
            elif x < seed:
                break
            else:
                x = (x * 3) + 1

        if seed % 1000001 == 0:
            # Log the seed, diagnostic, iteration, and printed count
            logging.info(f"seed: {seed}" f" diagnostic: {int(x)}" f" iteration: {seed - init_seed}" f" printed: {((seed - init_seed) // 1000001) + 1} times")
            print('\n\nseed:', seed, '\ndiagnostic:', int(x), '\niteration:', seed - init, '\nprinted', int(((seed - init) / 1000001) + 1) // 2, 'times, at', d.datetime.now())

            # Log with info but without extra formatting (log info without print)
            logging.info(f"Seed saved to {SAVE_FILE}")
            # Save main file
            try:
                with open(SAVE_FILE, 'w') as file:
                    lock_file(file)
                    file.write(str(seed))
                    unlock_file(file)
            except IOError:
                logging.error(f"ERROR: Failed to write to {SAVE_FILE}")

            # Save backup file every 10th save
            if seed % 11 == 0:
                try:
                    with open(BACKUP_FILE, 'w') as file:
                        lock_file(file)
                        file.write(str(seed))
                        unlock_file(file)
                        logging.info(f"Seed saved to backup file {BACKUP_FILE}")
                except IOError:
                    logging.error(f"ERROR: Failed to write to {BACKUP_FILE}")


# Timeout handler
def handle_timeout(start_time, seed):
    elapsed_time = time.time() - start_time
    if elapsed_time > TIMEOUT_LIMIT:
        logging.error("ERR: TIMEOUT | SAVING")
        try:
            with open(TIMEOUT_FILE, 'w') as file:
                file.write(str(seed))
                logging.info(f"Seed saved to timeout file {TIMEOUT_FILE}")
        except IOError:
            logging.error(f"ERROR: Failed to write to {TIMEOUT_FILE}")
        return True
    return False


# Start process function
def start_process():
    init_seed = init
    seed = init_seed

    start_time = time.time()  # Start time for timeout

    # Run main process
    main_process(init_seed, seed)

    # Check for timeout every second
    while True:
        if handle_timeout(start_time, seed):
            break


if __name__ == '__main__':
    logging.info("Starting the program.")
    start_process()
