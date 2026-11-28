import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

from Signaux_3_Lune import analyser_lune

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False


def nettoyer_chemin(raw: str) -> str:
    # Nettoie les accolades Windows
    chemin = raw.strip()
    if chemin.startswith("{") and chemin.endswith("}"):
        chemin = chemin[1:-1]
    return chemin


class AppLune:
    def __init__(self, root):
        self.root = root
        self.root.title("Signaux 3 — Analyse Lunaire (Drag & Drop)")
        self.root.geometry("460x240")
        self.root.resizable(False, False)

        self.hemisphere_var = tk.StringVar(value="N")

        titre = tk.Label(
            root,
            text="Détection de phase lunaire",
            font=("Segoe UI", 14, "bold"),
        )
        titre.pack(pady=(16, 4))

        zone = tk.Label(
            root,
            text="Glisse une image ici (PNG / JPG)\nou clique pour parcourir",
            font=("Segoe UI", 10),
            bg="#F1F5F9",
            fg="#0F172A",
            relief="groove",
            bd=2,
            width=44,
            height=5,
        )
        zone.pack(padx=20, pady=8)
        zone.bind("<Button-1>", self.choisir_fichier)

        if HAS_DND:
            zone.drop_target_register(DND_FILES)
            zone.dnd_bind("<<Drop>>", self.sur_drop)

        barre = tk.Frame(root)
        barre.pack(pady=(4, 12))

        tk.Label(barre, text="Hémisphère :", font=("Segoe UI", 9)).pack(side="left", padx=(0, 6))
        tk.Radiobutton(barre, text="Nord (N)", variable=self.hemisphere_var, value="N").pack(side="left")
        tk.Radiobutton(barre, text="Sud (S)", variable=self.hemisphere_var, value="S").pack(side="left")

    def choisir_fichier(self, _event=None):
        fichier = filedialog.askopenfilename(
            title="Choisir une photo de la Lune",
            initialdir="ImagesTest",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp"), ("Tous les fichiers", "*.*")],
        )
        if fichier:
            self.lancer_analyse(fichier)

    def sur_drop(self, event):
        premier = event.data.split()[0]
        chemin = nettoyer_chemin(premier)
        self.lancer_analyse(chemin)

    def lancer_analyse(self, chemin: str):
        p = Path(chemin)
        if not p.exists():
            messagebox.showerror("Fichier introuvable", f"Impossible de trouver :\n{chemin}")
            return
        try:
            analyser_lune(str(p), hemisphere=self.hemisphere_var.get(), afficher=True)
        except Exception as exc:
            messagebox.showerror("Erreur d'analyse", str(exc))


if __name__ == "__main__":
    root = TkinterDnD.Tk() if HAS_DND else tk.Tk()
    AppLune(root)
    root.mainloop()