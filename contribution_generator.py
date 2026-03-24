import os
import random
import subprocess
import csv
from datetime import datetime, timedelta
import torch

# ==================== CONFIGURACIÓN ====================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(SCRIPT_DIR, "contributions.csv")
LOG_FILE = os.path.join(SCRIPT_DIR, "cronjob.log")
VENV_ACTIVATE = os.path.join(SCRIPT_DIR, ".venv", "bin", "activate")

today = datetime.now().strftime("%Y-%m-%d")

# Intentar usar GPU, fallback a CPU si falla
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Usando dispositivo: {DEVICE.upper()}")

# ==================== FUNCIONES AUXILIARES ====================

def validate_file():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline='') as f:
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
    with open(CSV_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["date"] == today:
                return int(row.get("contributions", 0))
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
    rows = []
    updated = False
    with open(CSV_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["date"] == today:
                row["contributions"] = str(num)
                updated = True
            rows.append(row)
    if not updated:
        rows.append({
            "date": today,
            "contributions": str(num),
            "daily_limit": str(random.randint(3, 12))
        })

    with open(CSV_FILE, "w", newline='') as f:
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
    with open(CSV_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["date"] == today:
                return int(row.get("daily_limit", random.randint(3, 12)))
    return random.randint(3, 12)

def should_execute():
    """60-65% de probabilidad de ejecutar"""
    return random.random() < 0.65

def generate_random_commit_message():
    """Genera mensaje con GPT-2. Usa CPU si CUDA falla."""
    print("4 - Generating random commit message...")
    try:
        from transformers import pipeline

        # Forzar dispositivo y optimizaciones ligeras
        generator = pipeline(
            "text-generation",
            model="openai-community/gpt2",
            device=0 if DEVICE == "cuda" else -1,   # 0 = primera GPU
            torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
        )

        prompt = """Generate a short Git commit message following the Conventional Commits standard.
Examples:
- feat(auth): add user authentication module
- fix(api): resolve null pointer exception
- docs(readme): update installation instructions
- chore(deps): upgrade dependencies

New commit message:"""

        generated = generator(
            prompt,
            max_new_tokens=60,
            num_return_sequences=1,
            temperature=0.85,
            top_p=0.9,
            top_k=50,
            truncation=True,
            do_sample=True,
        )

        text = generated[0]["generated_text"]

        # Extraer la parte después del último "- "
        if "- " in text:
            return text.rsplit("- ", 1)[-1].strip()
        else:
            # Fallback simple si falla el parsing
            return "chore: update project files"

    except Exception as e:
        print(f"Warning: Error generating message with AI: {e}")
        # Fallback seguro
        types = ["feat", "fix", "docs", "chore", "refactor", "test"]
        scopes = ["", "core", "ui", "api", "deps", "docs"]
        return f"{random.choice(types)}({random.choice(scopes)}): {random.choice(['update', 'improve', 'add', 'fix', 'refactor'])} project files"


def git_commit():
    """
    Stages all changes in the repository and commits them with a generated commit message.
    """
    print("3 - Staging changes...")
    subprocess.run(["git", "add", "."], cwd=SCRIPT_DIR, check=True)

    commit_message = generate_random_commit_message()
    result = subprocess.run(["git", "commit", "-m", commit_message],
                            cwd=SCRIPT_DIR, capture_output=True, text=True)

    if result.returncode != 0:
        if "nothing to commit" in result.stderr.lower():
            print("No changes to commit.")
        else:
            print("Commit failed:", result.stderr)
            raise subprocess.CalledProcessError(result.returncode, "git commit")


def git_push():
    result = subprocess.run(["git", "push"], cwd=SCRIPT_DIR,
                            capture_output=True, text=True)
    if result.returncode == 0:
        print("5 - Changes pushed to GitHub successfully.")
    else:
        print("Error pushing to GitHub:")
        print(result.stderr)

def update_cron_with_random_time():
    """Actualiza el cron para la próxima ejecución entre 15 y 45 minutos."""
    random_minutes = random.randint(15, 45)
    next_time = (datetime.now() + timedelta(minutes=random_minutes)).strftime("%M * * * *")

    python_path = subprocess.run(["which", "python3"], capture_output=True, text=True).stdout.strip()

    script_path = os.path.join(SCRIPT_DIR, "contribution_generator.py")

    # Comando completo con activación del venv
    new_cron_line = f"{next_time} source {VENV_ACTIVATE} && cd {SCRIPT_DIR} && {python_path} {script_path} >> {LOG_FILE} 2>&1\n"

    # Actualizar crontab (eliminar entrada anterior del script)
    cron_file = "/tmp/current_cron"
    subprocess.run(f"crontab -l > {cron_file} 2>/dev/null || true", shell=True)

    with open(cron_file, "r") as f:
        lines = f.readlines()

    with open(cron_file, "w") as f:
        for line in lines:
            # Remove the existing entry for `contribution_generator.py` if it exists
            if "contribution_generator.py" not in line:
                f.write(line)
        f.write(new_cron_line)

    subprocess.run(f"crontab {cron_file}", shell=True)
    os.remove(cron_file)

    print(f"Cron job actualizado: próxima ejecución en ~{random_minutes} minutos.")


# ==================== MAIN ====================
def main():
    """
    Orchestrates the entire process of making contributions to a Git repository.
    Reads the current number of contributions, checks if the daily limit is reached,
    decides whether to execute based on random chance, updates the number of contributions,
    commits and pushes the changes, and updates the cron job.
    """
    try:
        print(f"\n{datetime.now()} - Starting contribution process...")

        if not should_execute():
            print("Skipping execution based on random chance.")
            return

        os.chdir(SCRIPT_DIR)

        current = read_number()
        daily_limit = get_daily_limit()

        if current >= daily_limit:
            print(f"Daily limit reached ({current}/{daily_limit}). No more contributions today.")
            return

        write_number(current + 1)
        git_commit()
        git_push()
        update_cron_with_random_time()

    except Exception as e:
        error_msg = f"{datetime.now()} --- ERROR: {str(e)}"
        print(error_msg)
        with open(LOG_FILE, "a") as f:
            f.write(error_msg + "\n")
        # No hacemos exit(1) para que el cron siga funcionando

if __name__ == "__main__":
    main()
