from pathlib import Path
import re

path = Path("frontend/src/components/Layout.")
if not path.exists():
    raise SystemExit(f"Fichier introuvable : {path}")

text = path.read_text(encoding="utf-8")
original = text

# Cas fréquent : le lien est écrit directement sous la forme
# {link("/bureaux", "Bureaux", "...")}
pattern = re.compile(
    r'(?P<indent>\s*)\{link\("/bureaux",\s*"Bureaux",\s*"[^"]*"\)\}'
)

match = pattern.search(text)
if match:
    indent = match.group("indent")
    replacement = (
        f'{indent}{{estNational && link("/bureaux", "Bureaux", "")}}'
    )
    text = pattern.sub(replacement, text, count=1)
else:
    # Si le lien possède un autre troisième argument, chercher plus largement.
    pattern2 = re.compile(
        r'(?P<indent>\s*)\{link\("/bureaux",\s*"Bureaux",[^\n]*?\)\}'
    )
    match = pattern2.search(text)
    if match:
        indent = match.group("indent")
        text = pattern2.sub(
            f'{indent}{{estNational && link("/bureaux", "Bureaux", "")}}',
            text,
            count=1,
        )

if text != original:
    # S'assurer que Layout récupère estNational depuis AuthContext.
    if "estNational" not in text.split("useAuth", 1)[0] if "useAuth" in text else False:
        pass

    # Si le fichier contient un destructuring useAuth(), ajouter estNational
    # uniquement lorsqu'il n'est pas déjà présent dans ce destructuring.
    auth_pattern = re.compile(r'(const\s*\{)([^}]*)(\}\s*=\s*useAuth\(\);)')
    auth_match = auth_pattern.search(text)
    if auth_match and "estNational" not in auth_match.group(2):
        contenu = auth_match.group(2).strip()
        if contenu:
            contenu += ", estNational"
        else:
            contenu = "estNational"
        text = text[:auth_match.start(2)] + " " + contenu + " " + text[auth_match.end(2):]

    path.write_text(text, encoding="utf-8")
    print("Layout. corrigé : le lien Bureaux est réservé aux utilisateurs nationaux.")
else:
    print("Aucune modification automatique de Layout..")
    print('Recherchez la ligne contenant : link("/bureaux", "Bureaux", ...)')
    print('et entourez-la de : {estNational && ...}')
