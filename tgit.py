import os
import sys
import msvcrt
import subprocess

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    ENDC = '\033[0m'
    
repositories_dir = os.getcwd()
last_action_status = ""
ascii_art = r"""

 _________ __   __     ___   ___      _________ _______   ________ _________  
/________//__/\/__/\  /___/\/__/\    /________//______/\ /_______//________/\ 
\__.::.__\\  \ \: \ \_\::.\ \\ \ \   \__.::.__\\::::__\/_\__.::._\\__.::.__\/ 
   \::\ \  \::\_\::\/_/\:: \/_) \ \     \::\ \  \:\ /____/\ \::\ \   \::\ \   
    \::\ \  \_:::   __\/\:. __  ( (      \::\ \  \:\\_  _\/ _\::\ \__ \::\ \  
     \::\ \      \::\ \  \: \ )  \ \      \::\ \  \:\_\ \ \/__\::\__/\ \::\ \ 
      \__\/       \__\/   \__\/\__\/       \__\/   \_____\/\________\/  \__\/ 
                                                                              

By Domenico Valentino
"""



def is_git_installed():
    try:
        subprocess.run(["git", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')
    
def input_with_escape(prompt):
    print(prompt, end='', flush=True)
    entered_text = ''
    cursor_position = 0

    while True:
        if msvcrt.kbhit():
            key = msvcrt.getch()
            
            if key == b'\x1b':  # ESC key
                print('\nOperation cancelled.')
                return None
            elif key in [b'\r', b'\n']:  # Enter key
                print()
                return entered_text
            elif key == b'\x08':  # Backspace key
                if cursor_position > 0:
                    # Move cursor back, print space to delete the char, then move cursor back again
                    print('\b \b', end='', flush=True)
                    entered_text = entered_text[:cursor_position - 1] + entered_text[cursor_position:]
                    cursor_position -= 1
            elif key == b'\xe0' or key == b'\x00':  # Special keys (arrows, function keys, etc.)
                key = msvcrt.getch()  # Get the second byte of the key
                if key == b'M':  # Right arrow
                    if cursor_position < len(entered_text):
                        print(entered_text[cursor_position], end='', flush=True)
                        cursor_position += 1
                elif key == b'K':  # Left arrow
                    if cursor_position > 0:
                        print('\b', end='', flush=True)
                        cursor_position -= 1
            else:
                try:
                    char = key.decode('utf-8')
                    print(char, end='', flush=True)
                    entered_text = entered_text[:cursor_position] + char + entered_text[cursor_position:]
                    cursor_position += 1
                except UnicodeDecodeError:
                    pass  # Ignore decoding errors (e.g., special keys)

def draw_menu(options, current_highlight, status_message="", title=""):
    clear_screen()
    print(f"{Colors.YELLOW}{ascii_art}{Colors.ENDC}")
    if title:
        print(title)
        print()
    for i, option in enumerate(options):
        line = f"{Colors.BLUE}> [{option}{Colors.BLUE}] <{Colors.ENDC}" if i == current_highlight else option
        if i == current_highlight and status_message:
            line += f"  {status_message}"  # Append status message to the highlighted option
        print(line)
    print("\nUse Up/Down arrows to navigate; Enter to select; 'q' to quit.")

def get_input():
    global last_action_status
    last_action_status = ""  # Clear the status message
    # Wait for a keypress and handle arrow keys and Enter
    while True:
        if msvcrt.kbhit():
            key = msvcrt.getch()
            # Arrow keys are a sequence of 3 bytes
            if key == b'\x00' or key == b'\xe0':
                key = msvcrt.getch()  # Skip the first byte of the sequence
                if key == b'H':  # Up arrow
                    return 'up'
                elif key == b'P':  # Down arrow
                    return 'down'
            elif key == b'\r':  # Enter key
                return 'enter'
            elif key == b'q':  # Quit program
                return 'quit'
            elif key == b'\x1b':
                return 'esc'
            else:
                return key.decode('utf-8')

def repository_menu(repo_name):
    global last_action_status
    repo_path = os.path.join(os.getcwd(), repo_name)
    current_highlight = 0

    while True:
        branch = subprocess.run(["git", "-C", repo_path, "branch", "--show-current"], check=True, stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
        title = f"{Colors.CYAN}Repository: {Colors.GREEN}{repo_name} {Colors.ENDC}(Branch: {Colors.YELLOW}{branch}{Colors.ENDC})"
        options = [
            f"{Colors.GREEN}Change Branch{Colors.ENDC}",
            f"{Colors.BLUE}Commit and Sync{Colors.ENDC}",
            f"{Colors.YELLOW}Pull{Colors.ENDC}",
            f"{Colors.RED}Discard Changes{Colors.ENDC}",
            f"{Colors.MAGENTA}Return to Main Menu{Colors.ENDC}"
        ]
        draw_menu(options, current_highlight, title=title, status_message=last_action_status)
        action = get_input()

        if action == 'up':
            current_highlight = (current_highlight - 1) % len(options)
        elif action == 'down':
            current_highlight = (current_highlight + 1) % len(options)
        elif action == 'esc':
            break
        elif action == 'enter':
            last_action_status = ""  # Clear the status message before performing an action
            if current_highlight == 0:  # Change Branch
                change_branch(repo_path)
            elif current_highlight == 1:  # Commit and Sync
                commit_and_sync(repo_path)
            elif current_highlight == 2:  # Pull
                pull(repo_path)
            elif current_highlight == 3:  # Discard Changes
                discard_changes(repo_path)
            elif current_highlight == 4:  # Return to Main Menu
                break
        elif action == 'quit':
            sys.exit()
    pass

            
def list_cloned_repositories():
    # return the list of cloned repositories IF .git folder exists
    cloned_repos = []
    for item in os.listdir(repositories_dir):
        if os.path.isdir(item) and os.path.exists(os.path.join(item, '.git')):
            cloned_repos.append(item)
    return cloned_repos

def delete_branch(repo_path, branches):
    global last_action_status

    print("Select a branch to delete:")
    for i, branch in enumerate(branches):
        print(f"{i + 1}. {branch}")

    branch_index = input_with_escape("Enter the number of the branch to delete: ")
    if not branch_index or not branch_index.isdigit() or int(branch_index) > len(branches):
        last_action_status = "\033[91mOperation cancelled or invalid selection.\033[0m"
        return

    branch_to_delete = branches[int(branch_index) - 1]

    confirm_delete = input_with_escape(f"Are you sure you want to delete the branch '{branch_to_delete}'? (y/n): ")
    if confirm_delete.lower() != 'y':
        last_action_status = "\033[91mBranch deletion cancelled.\033[0m"
        return

    try:
        subprocess.run(["git", "-C", repo_path, "branch", "-d", branch_to_delete], check=True)
        last_action_status = f"\033[92mBranch '{branch_to_delete}' successfully deleted.\033[0m"
    except subprocess.CalledProcessError:
        last_action_status = "\033[91mError: Failed to delete branch '{branch_to_delete}'.\033[0m"

def change_branch(repo_path):
    global last_action_status

    current_highlight = 0

    while True:
        branches_output = subprocess.run(["git", "-C", repo_path, "branch"], check=True, stdout=subprocess.PIPE).stdout.decode('utf-8').strip().split('\n')
        branches = [branch.strip().replace('*', Colors.GREEN + '*' + Colors.ENDC).strip() for branch in branches_output]

        create_option = f"{Colors.YELLOW}Create New Branch{Colors.ENDC}"
        delete_option = f"{Colors.RED}Delete a Branch{Colors.ENDC}"
        go_back_option = f"{Colors.MAGENTA}Return to Repository Menu{Colors.ENDC}"
        options = branches + [create_option, delete_option, go_back_option]

        title = "Change, Create, or Delete Branch"
        draw_menu(options, current_highlight, last_action_status, title=title)
        action = get_input()

        if action == 'up':
            current_highlight = (current_highlight - 1) % len(options)
        elif action == 'down':
            current_highlight = (current_highlight + 1) % len(options)
        elif action == 'esc':
            break
        elif action == 'enter':
            if current_highlight < len(branches):  # Switch to an existing branch
                branch_to_checkout = branches[current_highlight].replace(Colors.GREEN, "").replace(Colors.ENDC, "")
                subprocess.run(["git", "-C", repo_path, "checkout", branch_to_checkout], check=True)
                last_action_status = f"Switched to branch: {branch_to_checkout}"
                break
            elif current_highlight == len(branches):  # Create a new branch
                create_and_switch_branch(repo_path, branches, 0)  # Using the first branch as the base
                break
            elif current_highlight == len(branches) + 1:  # Delete a branch
                delete_branch(repo_path, branches)
                break
            elif current_highlight == len(branches) + 2:
                break
        elif action == 'quit':
            sys.exit()
    pass

def create_and_switch_branch(repo_path, existing_branches, highlight_index):
    global last_action_status

    # Use the highlighted branch as the base for the new branch
    base_branch = existing_branches[highlight_index]

    branch_name = input_with_escape(f"Enter the name of the new branch (branching from {base_branch}): ")
    if not branch_name:
        last_action_status = "\033[91mOperation cancelled.\033[0m"
        return

    try:
        subprocess.run(["git", "-C", repo_path, "checkout", "-b", branch_name, base_branch], check=True)
        last_action_status = f"\033[92mSuccess: New branch '{branch_name}' created from '{base_branch}'.\033[0m"

        checkout_confirm = input_with_escape("Do you want to checkout to the new branch? (y/n): ")
        if checkout_confirm.lower() == 'y':
            subprocess.run(["git", "-C", repo_path, "checkout", branch_name], check=True)
            last_action_status += " Checked out to new branch."
        else:
            last_action_status += " Staying on the current branch."

    except subprocess.CalledProcessError:
        last_action_status = "\033[91mError: Failed to create and switch to branch.\033[0m"

def commit_and_sync(repo_path):
    global last_action_status
    commit_message = input_with_escape("Enter the commit message: ")
    if not commit_message:
        last_action_status = "\033[91mOperation cancelled.\033[0m"
        return
    try:
        subprocess.run(["git", "-C", repo_path, "add", "*"], check=True)
        subprocess.run(["git", "-C", repo_path, "commit", "-am", commit_message], check=True)
        subprocess.run(["git", "-C", repo_path, "push"], check=True)
        last_action_status = "\033[92mSuccess: Changes committed and synced.\033[0m"
    except subprocess.CalledProcessError:
        last_action_status = "\033[91mError: Failed to commit and sync changes.\033[0m"
    pass

def pull(repo_path):
    global last_action_status
    try:
        subprocess.run(["git", "-C", repo_path, "pull"], check=True)
        last_action_status = "\033[92mSuccess: Repository updated.\033[0m"
    except subprocess.CalledProcessError:
        last_action_status = "\033[91mError: Failed to pull repository.\033[0m"
    pass

def discard_changes(repo_path):
    global last_action_status
    confirm = input_with_escape("Are you sure you want to discard all changes? (y/n): ")
    if not confirm:
        last_action_status = "\033[91mOperation cancelled.\033[0m"
        return
    if confirm.lower() == 'y':
        try:
            subprocess.run(["git", "-C", repo_path, "reset", "--hard"], check=True)
            last_action_status = "\033[92mSuccess: Changes discarded.\033[0m"
        except subprocess.CalledProcessError:
            last_action_status = "\033[91mError: Failed to discard changes.\033[0m"
    else:
        last_action_status = "\033[91mOperation cancelled.\033[0m"
    pass
    
def clone_repository():
    global last_action_status
    repo_url = input_with_escape("Enter the repository URL to clone: ")
    if not repo_url:
        last_action_status = "\033[91mOperation cancelled.\033[0m"
        return
    if not repo_url.startswith("https//github.com/") and not repo_url.endswith(".git"):
        last_action_status = "\033[91mError: Invalid repository URL.\033[0m"
        return
    try:
        subprocess.run(["git", "clone", repo_url], check=True)
        last_action_status = "\033[92mSuccess: Repository cloned.\033[0m"
    except subprocess.CalledProcessError:
        last_action_status = "\033[91mError: Failed to clone repository.\033[0m"


def authorize_github():
    global last_action_status
    user_name = input_with_escape("Enter your GitHub username: ")
    if not user_name:
        last_action_status = "\033[91mOperation cancelled.\033[0m"
        return
    user_email = input_with_escape("Enter your GitHub email: ")
    if not user_email:
        last_action_status = "\033[91mOperation cancelled.\033[0m"
        return
    if user_email and not '@' in user_email:
        last_action_status = "\033[91mError: Invalid email.\033[0m"
        return
    try:
        subprocess.run(["git", "config", "--global", "user.name", user_name], check=True)
        subprocess.run(["git", "config", "--global", "user.email", user_email], check=True)
        last_action_status = "\033[92mSuccess: GitHub authorization set.\033[0m"
    except subprocess.CalledProcessError:
        last_action_status = "\033[91mError: Failed to set GitHub authorization.\033[0m"
    pass


def show_help():
    #change screen to a help screen with all the commands and what they do and how to use them and how to exit and the credits
    clear_screen()
    print(f"{Colors.YELLOW}{ascii_art}{Colors.ENDC}")
    print(f"""{Colors.CYAN}Help Menu{Colors.ENDC}
    {Colors.WHITE}Use Up/Down arrows to navigate; Enter to select; 'q' to quit.{Colors.ENDC}
    {Colors.GREEN}Clone Repository:{Colors.ENDC} Clones a repository from GitHub
    {Colors.GREEN}Authorize GitHub:{Colors.ENDC} Authorizes the user's GitHub account
    {Colors.GREEN}Help:{Colors.ENDC} Shows this help menu
    {Colors.GREEN}Exit:{Colors.ENDC} Exits the program
    {Colors.BLUE}Change Branch:{Colors.ENDC} Changes the current branch of a repository
    {Colors.BLUE}Commit and Sync:{Colors.ENDC} Commits, stages, and syncs changes to a repository
    {Colors.BLUE}Pull:{Colors.ENDC} Pulls changes from a repository
    {Colors.RED}Discard Changes:{Colors.ENDC} Discards all changes to a repository
    {Colors.MAGENTA}Return to Main Menu:{Colors.ENDC} Returns to the main menu
    {Colors.YELLOW}At any input prompt, press the ESC key to cancel the operation{Colors.ENDC}
    {Colors.YELLOW}Press any key to return to the main menu{Colors.ENDC}""")
    msvcrt.getch()
    pass
    
def show_settings():
    global repositories_dir, last_action_status
    clear_screen()
    print(f"{Colors.YELLOW}{ascii_art}{Colors.ENDC}")
    print(f"{Colors.YELLOW}Settings{Colors.ENDC}\n")
    print(f"Current repositories directory: {Colors.CYAN}{repositories_dir}{Colors.ENDC}")
    new_dir = input_with_escape("Enter new path for repositories (or press ESC to cancel): ")

    if new_dir is None:
        last_action_status = "\033[91mOperation cancelled.\033[0m"
        return
    
    if not new_dir:
        last_action_status = "\033[91mError: Path cannot be empty.\033[0m"
        return

    if not os.path.exists(new_dir):
        try:
            os.makedirs(new_dir)
            last_action_status = f"\033[92mDirectory created: {new_dir}\033[0m"
        except Exception as e:
            last_action_status = f"\033[91mError: {str(e)}\033[0m"
            return
    elif not os.path.isdir(new_dir):
        last_action_status = "\033[91mError: Path is not a directory.\033[0m"
        return

    repositories_dir = new_dir
    last_action_status = f"\033[92mRepositories directory updated to: {new_dir}\033[0m"

def main_menu():
    global last_action_status
    base_options = [
        f"{Colors.CYAN}Clone Repository{Colors.ENDC}",
        f"{Colors.GREEN}Authorize GitHub{Colors.ENDC}",
        f"{Colors.YELLOW}Help{Colors.ENDC}",
        f"{Colors.YELLOW}Settings{Colors.ENDC}",
        f"{Colors.RED}Exit{Colors.ENDC}"
    ]

    current_highlight = 0
    
    # Check if Git is installed and show a warning if it is not, ask the user if they want to go to the Git website
    if not is_git_installed():
        print("Warning: Git is not installed. Some features will not work.")
        confirm = input_with_escape("Would you like to auto-install Git-Scm? (y/n): ")
        if confirm.lower() == 'y':
            subprocess.run(["winget", "install", "--id", "Git.Git", "-e", "--source", "winget"], check=True)
            last_action_status = "\033[92mSuccess: Winget executed.\033[0m"
        else:
            last_action_status = "\033[91mWarning: Git is not installed.\033[0m"

    while True:
        cloned_repos = list_cloned_repositories()
        # Apply color to each cloned repository
        colored_cloned_repos = [f"{Colors.CYAN}{repo}{Colors.ENDC}" for repo in cloned_repos]
        options = base_options + colored_cloned_repos
        draw_menu(options, current_highlight, last_action_status)
        action = get_input()

        if action == 'up':
            current_highlight = (current_highlight - 1) % len(options)
        elif action == 'down':
            current_highlight = (current_highlight + 1) % len(options)
        elif action == 'enter':
            if current_highlight == 0:  # Clone Repository
                clone_repository()
            elif current_highlight == 1:  # Authorize GitHub
                authorize_github()
            elif current_highlight == 2:
                show_help()
            elif current_highlight == 3:
                show_settings()
            elif current_highlight == 4:  # Exit
                break
            elif current_highlight > 4:  # Handle cloned repository options
                repo_name = options[current_highlight]
                repository_menu(repo_name)
        elif action == 'quit':
            clear_screen()
            sys.exit()

if __name__ == '__main__':
    main_menu()