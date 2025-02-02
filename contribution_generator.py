import os
import random
import subprocess
import csv
from datetime import datetime, timedelta

def validate_file():
    """
    Ensures that the 'contributions.csv' file exists.
    If the file does not exist, it creates the file and writes the header row.
    """
    if not os.path.exists("contributions.csv"):
        with open("contributions.csv", "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["date", "contributions", "daily_limit"])

def read_number():
    """
    Reads the number of contributions made on the current day from 'contributions.csv'.
    If the file or entry does not exist, it returns 0.

    Returns:
        int: The number of contributions made today.
    """
    print("1 - Reading number from file...")
    validate_file()
    today = datetime.now().strftime("%Y-%m-%d")
    with open("contributions.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["date"] == today:
                return int(row["contributions"])
    return 0

def write_number(num):
    """
    Writes the number of contributions for the current day to 'contributions.csv'.
    If an entry for the current day exists, it updates the entry.
    Otherwise, it adds a new entry.

    Args:
        num (int): The number of contributions to write.
    """
    print("2 - Writing number to file...")
    validate_file()
    today = datetime.now().strftime("%Y-%m-%d")
    rows = []
    updated = False
    with open("contributions.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["date"] == today:
                row["contributions"] = num
                updated = True
            rows.append(row)
    if not updated:
        rows.append({"date": today, "contributions": num, "daily_limit": random.randint(3, 12)})
    with open("contributions.csv", "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["date", "contributions", "daily_limit"])
        writer.writeheader()
        writer.writerows(rows)

def get_daily_limit():
    """
    Retrieves the daily contribution limit for the current day from 'contributions.csv'.
    If no entry exists for the current day, it generates a random limit.

    Returns:
        int: The daily contribution limit.
    """
    validate_file()
    today = datetime.now().strftime("%Y-%m-%d")
    with open("contributions.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["date"] == today:
                return int(row["daily_limit"])
    return random.randint(3, 12)

def should_execute():
    """
    Determines whether the script should execute based on a random chance.

    Returns:
        bool: True if the script should execute, False otherwise.
    """
    return random.random() < 0.65

def generate_random_commit_message():
    """
    Generates a random commit message following the Conventional Commits standard
    using a pre-trained GPT-2 model from the transformers library.

    Returns:
        str: The generated commit message.

    Raises:
        ValueError: If the generated text does not contain a valid commit message.
    """
    print("4 - Generating random commit message...")
    from transformers import pipeline

    generator = pipeline(
        "text-generation",
        model="openai-community/gpt2",
    )
    prompt = """
        Generate a Git commit message following the Conventional Commits standard. The message should include a type, an optional scope, and a subject. Please keep it short. Here are some examples:

        - feat(auth): add user authentication module
        - fix(api): resolve null pointer exception in user endpoint
        - docs(readme): update installation instructions
        - chore(deps): upgrade lodash to version 4.17.21
        - refactor(utils): simplify date formatting logic

        Now, generate a new commit message:
    """
    generated = generator(
        prompt,
        max_new_tokens=50,
        num_return_sequences=1,
        temperature=0.9,  # Slightly higher for creativity
        top_k=50,  # Limits sampling to top 50 logits
        top_p=0.9,  # Nucleus sampling for diversity
        truncation=True,
    )
    text = generated[0]["generated_text"]

    if "- " in text:
        return text.rsplit("- ", 1)[-1].strip()
    else:
        raise ValueError(f"Unexpected generated text {text}")

def git_commit():
    """
    Stages all changes in the repository and commits them with a generated commit message.
    """
    print("3 - Staging changes...")
    subprocess.run(["git", "add", "."])
    commit_message = generate_random_commit_message()
    subprocess.run(["git", "commit", "-m", commit_message])

def git_push():
    """
    Pushes the committed changes to the remote Git repository.
    Prints an error message if the push fails.
    """
    result = subprocess.run(["git", "push"], capture_output=True, text=True)
    if result.returncode == 0:
        print("5 - Changes pushed to GitHub successfully.")
    else:
        print("Error pushing to GitHub:")
        print(result.stderr)

def update_cron_with_random_time():
    """
    Updates the cron job to run the script at a random time within the next 15 to 45 minutes.
    Ensures the script is executed within the correct directory and updates the crontab accordingly.
    """
    current_number = read_number()
    daily_limit = get_daily_limit()

    if current_number >= daily_limit:
        print("Daily limit reached. No more contributions will be made today.")
        return

    if not should_execute():
        print("4 - Skipping execution based on random chance.")
        return

    # Generate random minute (0-59) within the range of 15 to 45 minutes
    random_minute = random.randint(15, 45)
    next_run_time = (datetime.now() + timedelta(minutes=random_minute)).strftime("%M * * * *")

    python_path = subprocess.run(["which", "python3"], capture_output=True, text=True).stdout.strip()

    # Define the new cron job command
    script_dir = os.path.dirname(os.path.abspath(__file__))
    git_repo_dir = "/path/to/your/git/repository"  # Update this path to your Git repository
    script_path = os.path.join(script_dir, 'contribution_generator.py')
    log_file = os.path.join(script_dir, 'cronjob.log')

    # Define the new cron job command with the correct working directory
    new_cron_command = f"cd {git_repo_dir} && {python_path} {script_path} >> {datetime.now(), log_file} 2>&1\n"

    # Get the current crontab
    cron_file = "/tmp/current_cron"
    os.system(
        f"crontab -l > {cron_file} 2>/dev/null || true"
    )  # Save current crontab, or create a new one if empty

    # Update the crontab file
    with open(cron_file, "r") as file:
        lines = file.readlines()

    with open(cron_file, "w") as file:
        for line in lines:
            # Remove existing entry for `contribution_generator.py` if it exists
            if "contribution_generator.py" not in line:
                file.write(line)
        # Add the new cron job at the random time
        file.write(new_cron_command)

    # Load the updated crontab
    os.system(f"crontab {cron_file}")
    os.remove(cron_file)

    print(f"Cron job updated to run every {random_minute} minutes.")


def main():
    """
    Orchestrates the entire process of making contributions to a Git repository.
    Reads the current number of contributions, checks if the daily limit is reached,
    decides whether to execute based on random chance, updates the number of contributions,
    commits and pushes the changes, and updates the cron job.
    """
    try:
        current_number = read_number()
        daily_limit = get_daily_limit()

        if current_number >= daily_limit:
            print("Daily limit reached. No more contributions will be made today.")
            return

        if not should_execute():
            print("2 - Skipping execution based on random chance.")
            print("EXIT.")
            return

        new_number = current_number + 1
        write_number(new_number)
        git_commit()
        git_push()
        update_cron_with_random_time()
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()
