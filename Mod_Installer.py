import customtkinter as ctk
import requests
import subprocess
import os
import shutil
import zipfile
import sys

# Globale Variablen
JAVA_DOWNLOAD_URL = "https://download.oracle.com/java/20/latest/jdk-20_windows-x64_bin.exe"
NEOFORGE_URL = "https://maven.neoforged.net/releases/net/neoforged/forge/20.4.238/forge-20.4.238-installer.jar"
MODS_URL = "https://www.dropbox.com/scl/fi/vyt3exbdpz66973jbkmf7/mods.zip?rlkey=yq9omkh1vyjwmzx0rybl8sugj&st=tjdbpi6c&dl=1"
VERSION_URL = "https://www.dropbox.com/scl/fi/gqymxbhbo7b0nmd9bcqyj/version.txt?rlkey=quoax3idebv6r0vht29qzfpwr&st=7gxx8ygf&dl=1"  # Hier den Link zur Version-Datei einfügen
UPDATE_URL = "https://example.com/latest_installer.exe"  # Hier den Link zur neuesten Exe einfügen
CURRENT_VERSION = "1.0.0"
TEMP_FOLDER = os.path.join(os.getenv("TEMP"), "minecraft_installer")
MINECRAFT_FOLDER = os.path.join(os.getenv('APPDATA'), ".minecraft")
MODS_FOLDER = os.path.join(MINECRAFT_FOLDER, "mods")

class InstallerApp:
    def __init__(self, root):
        ctk.set_appearance_mode("System")  # "Dark" oder "Light"
        ctk.set_default_color_theme("blue")  # Alternativen: "green", "dark-blue"

        self.root = root
        self.root.title("Minecraft Mod Installer")
        self.root.geometry("600x600")
        self.center_window(self.root, 600, 600)

        self.check_for_updates()

        # Anleitung
        instructions = (
            "1. Klicken Sie auf 'Check for Java'.\n"
            "1.1. Wenn Java nicht installiert ist, wird die Schaltfläche Rot. Klicke auf 'Install Java'.\n"
            "2. Klicken Sie auf 'Check for NeoForge'.\n"
            "2.1. Wenn NeoForge nicht installiert ist, wird die Schaltfläche Rot. Klicke auf 'Install NeoForge'.\n"
            "2.2. Es öffnet sich nach kurzer Zeit der 'NeoForge Installer'.\n"
            "      Dort einfach die Schaltfläche 'proceed' anklicken!\n"
            "3. Klicken Sie auf 'Install Mods', um die Mods herunterzuladen und zu installieren."
        )
        ctk.CTkLabel(self.root, text="Minecraft Mod Installer", font=("Arial", 20)).pack(pady=10)
        ctk.CTkLabel(self.root, text=instructions, font=("Arial", 12), wraplength=550).pack(pady=5)

        # Buttons
        buttons_frame = ctk.CTkFrame(self.root)
        buttons_frame.pack(pady=10)

        self.java_button = ctk.CTkButton(buttons_frame, text="Check for Java", command=self.check_java, width=200)
        self.java_button.grid(row=0, column=0, padx=10, pady=5)

        self.neoforge_button = ctk.CTkButton(buttons_frame, text="Check for NeoForge", command=self.check_neoforge, width=200)
        self.neoforge_button.grid(row=0, column=1, padx=10, pady=5)

        ctk.CTkButton(buttons_frame, text="Install Java", command=self.install_java, width=200).grid(row=1, column=0, padx=10, pady=5)
        ctk.CTkButton(buttons_frame, text="Install NeoForge", command=self.install_neoforge, width=200).grid(row=1, column=1, padx=10, pady=5)

        self.progress_label = ctk.CTkLabel(self.root, text="Progress: 0%", font=("Arial", 12))
        self.progress_label.pack(pady=5)

        self.progress_bar = ctk.CTkProgressBar(self.root)
        self.progress_bar.set(0)  # Fortschrittsleiste auf 0 setzen
        self.progress_bar.pack(pady=5)

        ctk.CTkButton(self.root, text="Install Mods", command=self.install_mods, width=450).pack(pady=15)

        # Copyright Label
        ctk.CTkLabel(self.root, text="© Julian Menke", font=("Arial", 10)).pack(side="left", anchor="sw", padx=10, pady=10)

    def center_window(self, window, width, height):
        """Zentriert das Fenster auf dem Bildschirm."""
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")
        window.lift()
        window.attributes('-topmost', True)
        window.after_idle(window.attributes, '-topmost', False)

    def update_progress(self, value, total):
        percent = int((value / total) * 100)
        self.progress_label.configure(text=f"Progress: {percent}%")
        self.progress_bar.set(value / total)
        self.root.update_idletasks()

    def check_for_updates(self):
        """Prüft, ob eine neue Version verfügbar ist."""
        try:
            response = requests.get(VERSION_URL)
            latest_version = response.text.strip()

            if latest_version != CURRENT_VERSION:
                if self.prompt_update(latest_version):
                    self.download_and_replace(latest_version)
        except Exception as e:
            print(f"Fehler beim Überprüfen von Updates: {e}")

    def prompt_update(self, latest_version):
        """Zeigt ein Update-Dialogfenster an."""
        toplevel = ctk.CTkToplevel(self.root)
        toplevel.title("Update verfügbar")
        toplevel.geometry("400x200")
        self.center_window(toplevel, 400, 200)

        ctk.CTkLabel(
            toplevel,
            text=f"Eine neue Version ({latest_version}) ist verfügbar. Möchten Sie das Update installieren?",
            wraplength=350,
            font=("Arial", 12),
        ).pack(pady=20)

        def accept_update():
            toplevel.destroy()
            return True

        def decline_update():
            toplevel.destroy()
            return False

        ctk.CTkButton(toplevel, text="Ja", command=accept_update).pack(side="left", padx=10, pady=20)
        ctk.CTkButton(toplevel, text="Nein", command=decline_update).pack(side="right", padx=10, pady=20)

    def download_and_replace(self, latest_version):
        """Lädt die neue Version herunter und ersetzt die aktuelle."""
        try:
            response = requests.get(UPDATE_URL, stream=True)
            update_path = os.path.join(TEMP_FOLDER, "latest_installer.exe")

            with open(update_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            subprocess.Popen([update_path])
            self.root.quit()
        except Exception as e:
            print(f"Fehler beim Herunterladen des Updates: {e}")

    def check_java(self):
        """Prüft, ob Java installiert ist."""
        java_installed = subprocess.call("java -version", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0
        if java_installed:
            self.java_button.configure(fg_color="green")
        else:
            self.java_button.configure(fg_color="red")

    def install_java(self):
        """Installiert Java."""
        java_installer_path = os.path.join(TEMP_FOLDER, "java_installer.exe")
        response = requests.get(JAVA_DOWNLOAD_URL, stream=True)
        total_length = int(response.headers.get('content-length', 0))
        downloaded = 0

        with open(java_installer_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                self.update_progress(downloaded, total_length)

        subprocess.run([java_installer_path, "/s"], check=True)
        self.java_button.configure(fg_color="green")

    def check_neoforge(self):
        """Prüft, ob NeoForge installiert ist."""
        neoforge_installed = os.path.exists(os.path.join(MINECRAFT_FOLDER, "versions", "neoforge-20.4.238"))
        if neoforge_installed:
            self.neoforge_button.configure(fg_color="green")
        else:
            self.neoforge_button.configure(fg_color="red")

    def install_neoforge(self):
        """Installiert NeoForge."""
        forge_installer_path = os.path.join(TEMP_FOLDER, "neoforge_installer.jar")
        response = requests.get(NEOFORGE_URL, stream=True)
        total_length = int(response.headers.get('content-length', 0))
        downloaded = 0

        with open(forge_installer_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                self.update_progress(downloaded, total_length)

        subprocess.run(["java", "-jar", forge_installer_path], check=True)
        self.neoforge_button.configure(fg_color="green")

    def install_mods(self):
        """Lädt Mods herunter und verschiebt sie in den Minecraft-Mods-Ordner."""
        if not os.path.exists(MODS_FOLDER):
            os.makedirs(MODS_FOLDER)

        mods_zip_path = os.path.join(TEMP_FOLDER, "mods.zip")
        response = requests.get(MODS_URL, stream=True)
        if response.status_code != 200:
            self.show_toplevel_message("Fehler", "Mods konnten nicht heruntergeladen werden.")
            return

        total_length = int(response.headers.get('content-length', 0))
        downloaded = 0

        with open(mods_zip_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                self.update_progress(downloaded, total_length)

        try:
            with zipfile.ZipFile(mods_zip_path, 'r') as zip_ref:
                zip_ref.extractall(TEMP_FOLDER)
        except zipfile.BadZipFile:
            self.show_toplevel_message("Fehler", "Die heruntergeladene Mods-Datei ist ungültig.")
            return

        for mod_file in os.listdir(TEMP_FOLDER):
            if mod_file.endswith(".jar"):
                mod_destination = os.path.join(MODS_FOLDER, mod_file)
                if os.path.exists(mod_destination):
                    os.remove(mod_destination)
                shutil.move(os.path.join(TEMP_FOLDER, mod_file), mod_destination)

        self.show_toplevel_message("Mods", "Mods wurden erfolgreich installiert!")

# Starte die GUI
if __name__ == "__main__":
    root = ctk.CTk()
    app = InstallerApp(root)
    root.mainloop()
