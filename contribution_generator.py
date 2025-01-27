import os
import random
import subprocess
import csv
from datetime import datetime, timedelta

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

def validate_file():
    if not os.path.exists("contributions.csv"):
        with open("contributions.csv", "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["date", "contributions", "daily_limit"])

def read_number():
    print("Reading number from file...")
    validate_file()
    today = datetime.now().strftime("%Y-%m-%d")
    with open("contributions.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["date"] == today:
                return int(row["contributions"])
    return 0

def write_number(num):
    print("Writing number to file...")
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
    validate_file()
    today = datetime.now().strftime("%Y-%m-%d")
    with open("contributions.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["date"] == today:
                return int(row["daily_limit"])
    return random.randint(3, 12)

def should_execute():
    return random.random() < 0.5

def generate_random_commit_message():
    print("Generating random commit message...")
    from transformers import pipeline

    generator = pipeline(
        "text-generation",
        model="openai-community/gpt2",
    )
    prompt = """
        Generate a Git commit message following the Conventional Commits standard. The message should include a type, an optional scope, and a subject.Please keep it short. Here are some examples:

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
    # Stage the changes
    print("Staging changes...")
    subprocess.run(["git", "add", "number.txt"])
    commit_message = generate_random_commit_message()
    subprocess.run(["git", "commit", "-m", commit_message])

def git_push():
    # Push the committed changes to GitHub
    result = subprocess.run(["git", "push"], capture_output=True, text=True)
    if result.returncode == 0:
        print("Changes pushed to GitHub successfully.")
    else:
        print("Error pushing to GitHub:")
        print(result.stderr)

def update_cron_with_random_time():
    current_number = read_number()
    daily_limit = get_daily_limit()

    if current_number >= daily_limit:
        print("Daily limit reached. No more contributions will be made today.")
        return

    if not should_execute():
        print("Skipping execution based on random chance.")
        return

    # Generate random minute (0-59) within the range of 15 to 45 minutes
    random_minute = random.randint(15, 45)
    next_run_time = (datetime.now() + timedelta(minutes=random_minute)).strftime("%M * * * *")

    # Define the new cron job command
    new_cron_command = f"{next_run_time} cd {script_dir} && python3 {os.path.join(script_dir, 'contribution_generator.py')}\n"

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
    try:
        current_number = read_number()
        daily_limit = get_daily_limit()

        if current_number >= daily_limit:
            print("Daily limit reached. No more contributions will be made today.")
            return

        if not should_execute():
            print("Skipping execution based on random chance.")
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