import os
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading

# Chemin du projet et de l'environnement virtuel
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(PROJECT_DIR, "venv")

def get_python_executable():
    """Renvoie le chemin de l'exécutable Python dans l'environnement virtuel."""
    return os.path.join(VENV_DIR, "Scripts" if os.name == "nt" else "bin", "python3")

def setup_venv():
    """Crée et configure l'environnement virtuel si nécessaire."""
    if not os.path.exists(VENV_DIR):
        print("Création de l'environnement virtuel...")
        subprocess.run([sys.executable, "-m", "venv", VENV_DIR], check=True)

    pip_executable = os.path.join(VENV_DIR, "Scripts" if os.name == "nt" else "bin", "pip")
    try:
        print("Installation des dépendances...")
        subprocess.run([pip_executable, "install", "-r", os.path.join(PROJECT_DIR, "requirements.txt")], check=True)
    except subprocess.CalledProcessError:
        raise RuntimeError("Erreur lors de l'installation des dépendances. Vérifiez le fichier requirements.txt.")

def run_command(command):
    """Exécute une commande en utilisant l'environnement virtuel."""
    python_executable = get_python_executable()
    full_command = [python_executable] + command
    try:
        subprocess.run(full_command, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Erreur lors de l'exécution de la commande : {e}")

def validate_inputs(box_threshold, text_threshold):
    """Valide les entrées utilisateur avant le traitement."""
    try:
        float(box_threshold)
        float(text_threshold)
    except ValueError:
        raise ValueError("Les valeurs numériques doivent être valides (ex. : 0.5, 1.0).")

def process_folder(root, start_folder, start_subfolder, translator="deep", language="FR", align_center=False, box_threshold=0.5, text_threshold=0.5, progress_bar=None):
    """Traite tous les fichiers du dossier de départ et des sous-dossiers dans l'ordre alphanumérique."""
    if not os.path.exists(start_folder):
        messagebox.showerror("Erreur", f"Le dossier spécifié '{start_folder}' n'existe pas.")
        return

    if start_subfolder and not os.path.exists(start_subfolder):
        messagebox.showerror("Erreur", f"Le sous-dossier spécifié '{start_subfolder}' n'existe pas.")
        return

    language = language.strip()

    common_args = [
        "-m", "manga_translator", "-v",
        f"--translator={translator}",
        f"-l", language,
        f"--box-threshold={box_threshold}",
        f"--text-threshold={text_threshold}",
    ]
    optional_args = [
        ("--align-center", align_center),
    ]
    common_args.extend([arg for arg, condition in optional_args if condition])

    # Obtenir la liste des sous-dossiers dans l'ordre alphanumérique
    subfolders = sorted(os.listdir(start_folder))

    # Trouver l'index du sous-dossier de départ
    start_index = 0
    if start_subfolder:
        start_index = subfolders.index(os.path.basename(start_subfolder))

    # Traiter les sous-dossiers à partir du sous-dossier de départ
    subfolders_to_process = subfolders[start_index:]

    files_to_process = []
    for subfolder in subfolders_to_process:
        subfolder_path = os.path.join(start_folder, subfolder)
        if os.path.isdir(subfolder_path):
            for root_dir, dirs, files in os.walk(subfolder_path):
                dirs.sort()
                files.sort()

                for file in files:
                    file_path = os.path.join(root_dir, file)
                    if file.endswith('.jpg') and not file.endswith('translated.jpg'):
                        files_to_process.append(file_path)
        else:
            if subfolder.endswith('.jpg') and not subfolder.endswith('translated.jpg'):
                files_to_process.append(os.path.join(start_folder, subfolder))

    # Ajouter les fichiers du dossier principal
    for file in os.listdir(start_folder):
        file_path = os.path.join(start_folder, file)
        if file.endswith('.jpg') and not file.endswith('translated.jpg'):
            files_to_process.append(file_path)

    total_files = len(files_to_process)
    if total_files == 0:
        messagebox.showwarning("Attention", "Aucun fichier à traiter.")
        return

    if progress_bar:
        progress_bar['maximum'] = total_files
        progress_bar['value'] = 0

    for i, file_path in enumerate(files_to_process):
        try:
            print(f"Début du traitement du fichier : {file_path}")
            run_command(common_args + ["-i", file_path])
            print(f"Fichier traité avec succès : {file_path}")

            if progress_bar:
                root.after(0, update_progress_bar, progress_bar, i + 1, total_files)

        except RuntimeError as e:
            print(f"Erreur lors du traitement du fichier '{file_path}': {e}")
            messagebox.showerror("Erreur", f"Échec du traitement du fichier '{file_path}': {e}")
            return

    if progress_bar:
        root.after(0, update_progress_bar, progress_bar, total_files, total_files)

    messagebox.showinfo("Succès", "Tous les fichiers ont été traités avec succès !")

def update_progress_bar(progress_bar, value, total_files):
    progress_bar['value'] = value
    percentage = (value / total_files) * 100
    progress_label.config(text=f"{int(percentage)}%")

def select_folder(entry):
    folder_path = filedialog.askdirectory(title="Choisir un dossier")
    if folder_path:
        entry.delete(0, tk.END)
        entry.insert(0, folder_path)

def start_processing():
    global_folder = global_folder_entry.get()
    start_subfolder = start_subfolder_entry.get()
    translator = translator_var.get()
    language = language_var.get()
    align_center = align_center_var.get()
    box_threshold = box_threshold_var.get()
    text_threshold = text_threshold_var.get()
    if not global_folder:
        messagebox.showwarning("Attention", "Veuillez sélectionner le dossier global avant de continuer.")
        return

    start_button.config(state=tk.DISABLED)

    processing_thread = threading.Thread(target=process_folder, args=(
        root, global_folder, start_subfolder, translator, language, align_center, box_threshold, text_threshold, progress_bar))
    processing_thread.start()

    root.after(100, check_processing_thread, processing_thread)

def check_processing_thread(thread):
    if thread.is_alive():
        root.after(100, check_processing_thread, thread)
    else:
        start_button.config(state=tk.NORMAL)

# Configuration de l'environnement virtuel
try:
    setup_venv()
except Exception as e:
    messagebox.showerror("Erreur", f"Impossible de configurer l'environnement virtuel : {e}")
    sys.exit(1)

# Création de l'interface graphique
root = tk.Tk()
root.title("FLEMME GUI DE Manga Translator")
root.geometry("600x600")

# Widgets pour sélectionner le dossier global
global_folder_label = tk.Label(root, text="Dossier global contenant les fichiers :")
global_folder_label.pack(pady=5)
global_folder_frame = tk.Frame(root)
global_folder_frame.pack(pady=5)
global_folder_entry = tk.Entry(global_folder_frame, width=50)
global_folder_entry.pack(side=tk.LEFT, padx=5)
global_browse_button = tk.Button(global_folder_frame, text="Parcourir", command=lambda: select_folder(global_folder_entry))
global_browse_button.pack(side=tk.RIGHT)

# Widgets pour sélectionner le sous-dossier de départ
start_subfolder_label = tk.Label(root, text="Sous-dossier de départ (optionnel) :")
start_subfolder_label.pack(pady=5)
start_subfolder_frame = tk.Frame(root)
start_subfolder_frame.pack(pady=5)
start_subfolder_entry = tk.Entry(start_subfolder_frame, width=50)
start_subfolder_entry.pack(side=tk.LEFT, padx=5)
start_browse_button = tk.Button(start_subfolder_frame, text="Parcourir", command=lambda: select_folder(start_subfolder_entry))
start_browse_button.pack(side=tk.RIGHT)

# Options et paramètres
translator_label = tk.Label(root, text="Traducteur :")
translator_label.pack(pady=5)
translator_var = tk.StringVar(value="deep")
translator_menu = tk.OptionMenu(root, translator_var, "deep", "youdao", "baidu", "papago", "caiyun", "none")
translator_menu.pack()

# Options de langue
language_label = tk.Label(root, text="Langue cible :")
language_label.pack(pady=5)
language_var = tk.StringVar(value="FRA")
language_entry = tk.Entry(root, textvariable=language_var)
language_entry.pack()

# Option d'alignement au centre
align_center_var = tk.BooleanVar(value=False)
align_center_check = tk.Checkbutton(root, text="Aligner le texte au centre", variable=align_center_var)
align_center_check.pack(pady=5)

# Option de seuil de boîte englobante
box_threshold_label = tk.Label(root, text="Seuil de boîte englobante :")
box_threshold_label.pack(pady=5)
box_threshold_var = tk.DoubleVar(value=0.2)
box_threshold_entry = tk.Entry(root, textvariable=box_threshold_var)
box_threshold_entry.pack()
box_threshold_desc = tk.Label(root, text="Augmentez cette valeur pour inclure plus de boîtes englobantes.", fg="gray", wraplength=400, justify="left")
box_threshold_desc.pack()

# Option de seuil de texte
text_threshold_label = tk.Label(root, text="Seuil de texte :")
text_threshold_label.pack(pady=5)
text_threshold_var = tk.DoubleVar(value=0.2)
text_threshold_entry = tk.Entry(root, textvariable=text_threshold_var)
text_threshold_entry.pack()
text_threshold_desc = tk.Label(root, text="Diminuez cette valeur pour inclure plus de zones de texte.", fg="gray", wraplength=400, justify="left")
text_threshold_desc.pack()

# Bouton de démarrage
start_button = tk.Button(root, text="Démarrer le traitement", command=start_processing)
start_button.pack(pady=20)

# Barre de progression
progress_bar = ttk.Progressbar(root, length=400, mode='determinate')
progress_bar.pack(pady=10)

# Label pour afficher le pourcentage
progress_label = tk.Label(root, text="0%", font=("Helvetica", 10))
progress_label.pack(pady=5)

# Bouton pour quitter
exit_button = tk.Button(root, text="Fermer l'application", command=root.quit)
exit_button.pack(pady=5)

# Lancement de l'interface
root.mainloop()

