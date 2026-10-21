"""Construit une APK Android installable qui embarque la page autonome de recherche.

Usage : python android/build_apk.py --page data/medicaments.html --out data/officine-sam.apk

Aucun SDK Android n'est nécessaire : seuls Java (JDK 11 ou plus récent) et Python sont requis.
- les classes Android pour la compilation viennent de `org.robolectric:android-all` (Maven Central) ;
- la conversion en dex utilise `com.jakewharton.android.repackaged:dalvik-dx` (outil dx d'Android, Maven Central) ;
- le manifeste binaire (AXML) est écrit par ce script ; l'application n'a pas de ressources compilées ;
- la signature est une signature v1 (jarsigner du JDK). D'où targetSdkVersion 29 : la signature v2 n'est
  exigée qu'à partir de la cible 30. Clé de test créée au premier lancement (data/android-test.keystore).
"""
import argparse
import pathlib
import shutil
import struct
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

HERE = pathlib.Path(__file__).resolve().parent
PACKAGE = "be.meddoc.officine"
LABEL = "Officine SAM"
MIN_SDK, TARGET_SDK = 21, 29
MAVEN = "https://maven-central.storage-download.googleapis.com/maven2"  # miroir officiel de Maven Central
DEPENDENCIES = {
    "android-all.jar": "org/robolectric/android-all/10-robolectric-5803371/android-all-10-robolectric-5803371.jar",
    "dx.jar": "com/jakewharton/android/repackaged/dalvik-dx/14.0.0_r21/dalvik-dx-14.0.0_r21.jar",
}
KEY_ALIAS, KEY_PASSWORD = "officine", "officine-sam-test"

# Identifiants des attributs android:* (table publique du framework, R.attr).
ATTR = {
    "label": 0x01010001, "name": 0x01010003, "exported": 0x01010010, "configChanges": 0x0101001F,
    "minSdkVersion": 0x0101020C, "versionCode": 0x0101021B, "versionName": 0x0101021C,
    "targetSdkVersion": 0x01010270, "allowBackup": 0x01010280, "hardwareAccelerated": 0x010102D3,
}
ANDROID_NS = "http://schemas.android.com/apk/res/android"
TYPE_STRING, TYPE_INT_DEC, TYPE_INT_HEX, TYPE_BOOLEAN = 0x03, 0x10, 0x11, 0x12


# ---------------------------------------------------------------- manifeste binaire (AXML)

def manifest_tree(version_code, version_name):
    """(balise, [(attribut android ?, nom, valeur)], enfants) du manifeste de l'application."""
    a = lambda name, value: (True, name, value)
    return ("manifest", [(False, "package", PACKAGE), a("versionCode", version_code), a("versionName", version_name)], [
        ("uses-sdk", [a("minSdkVersion", MIN_SDK), a("targetSdkVersion", TARGET_SDK)], []),
        ("uses-permission", [a("name", "android.permission.INTERNET")], []),
        ("application", [a("label", LABEL), a("allowBackup", False), a("hardwareAccelerated", True)], [
            ("activity", [a("name", PACKAGE + ".MainActivity"), a("exported", True),
                          a("configChanges", 0x04A0)], [  # orientation | keyboardHidden | screenSize
                ("intent-filter", [], [
                    ("action", [a("name", "android.intent.action.MAIN")], []),
                    ("category", [a("name", "android.intent.category.LAUNCHER")], []),
                ]),
            ]),
        ]),
    ])


def encode_manifest(tree):
    """Encode l'arbre au format XML binaire d'Android (même structure que celle produite par aapt)."""
    # Pool de chaînes : d'abord les noms d'attributs android (dans l'ordre de la table de ressources), puis le reste.
    attr_names, strings = [], []

    def walk(node):
        tag, attrs, children = node
        for is_android, name, _ in attrs:
            if is_android and name not in attr_names:
                attr_names.append(name)
        for child in children:
            walk(child)
    walk(tree)
    attr_names.sort(key=lambda n: ATTR[n])
    strings.extend(attr_names)

    def index(s):
        if s not in strings:
            strings.append(s)
        return strings.index(s)
    for s in ("android", ANDROID_NS):
        index(s)

    body = []

    def node_chunks(node, line=1):
        tag, attrs, children = node
        encoded = []
        ordered = sorted(attrs, key=lambda x: ATTR.get(x[1], 0) if x[0] else -1)
        for is_android, name, value in ordered:
            ns = index(ANDROID_NS) if is_android else 0xFFFFFFFF
            name_i = attr_names.index(name) if is_android else index(name)
            if isinstance(value, bool):
                raw, kind, data = 0xFFFFFFFF, TYPE_BOOLEAN, 0xFFFFFFFF if value else 0
            elif isinstance(value, int):
                raw, kind, data = 0xFFFFFFFF, TYPE_INT_HEX if name == "configChanges" else TYPE_INT_DEC, value
            else:
                raw = index(value)
                kind, data = TYPE_STRING, raw
            encoded.append(struct.pack("<IIIHBBI", ns, name_i, raw, 8, 0, kind, data))
        start = struct.pack("<IIIIHHHHHH", line, 0xFFFFFFFF, 0xFFFFFFFF, index(tag), 20, 20, len(encoded), 0, 0, 0)
        start += b"".join(encoded)
        body.append(struct.pack("<HHI", 0x0102, 16, 8 + len(start)) + start)
        for child in children:
            node_chunks(child, line + 1)
        end = struct.pack("<IIII", line, 0xFFFFFFFF, 0xFFFFFFFF, index(tag))
        body.append(struct.pack("<HHI", 0x0103, 16, 8 + len(end)) + end)

    namespace = struct.pack("<IIII", 1, 0xFFFFFFFF, index("android"), index(ANDROID_NS))
    node_chunks(tree)
    elements = (struct.pack("<HHI", 0x0100, 16, 24) + namespace + b"".join(body)
                + struct.pack("<HHI", 0x0101, 16, 24) + namespace)

    # Pool de chaînes UTF-16 : longueur (u16), caractères, terminateur nul.
    data, offsets = b"", []
    for s in strings:
        offsets.append(len(data))
        units = s.encode("utf-16-le")
        data += struct.pack("<H", len(units) // 2) + units + b"\x00\x00"
    data += b"\x00" * (-len(data) % 4)
    header_size = 28
    strings_start = header_size + 4 * len(strings)
    pool = struct.pack("<HHIIIIII", 0x0001, header_size, strings_start + len(data), len(strings), 0, 0,
                       strings_start, 0) + b"".join(struct.pack("<I", o) for o in offsets) + data
    resource_map = struct.pack("<HHI", 0x0180, 8, 8 + 4 * len(attr_names)) + b"".join(
        struct.pack("<I", ATTR[n]) for n in attr_names)
    content = pool + resource_map + elements
    return struct.pack("<HHI", 0x0003, 8, 8 + len(content)) + content


# ---------------------------------------------------------------- outils

def fetch_dependencies(directory):
    directory.mkdir(parents=True, exist_ok=True)
    for name, path in DEPENDENCIES.items():
        target = directory / name
        if not target.exists():
            print(f"Téléchargement de {name}…")
            with urllib.request.urlopen(f"{MAVEN}/{path}", timeout=600) as r, open(target, "wb") as f:
                shutil.copyfileobj(r, f)
    return {name: directory / name for name in DEPENDENCIES}


def run(*args):
    subprocess.run([str(a) for a in args], check=True)


def ensure_keystore(path):
    if not path.exists():
        run("keytool", "-genkeypair", "-keystore", path, "-storepass", KEY_PASSWORD, "-keypass", KEY_PASSWORD,
            "-alias", KEY_ALIAS, "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000",
            "-dname", "CN=Officine SAM (test), O=med.doc, C=BE")
    return path


def build(page, out, deps_dir, keystore, version_code=1, version_name="1.0"):
    deps = fetch_dependencies(deps_dir)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        classes = tmp / "classes"
        classes.mkdir()
        sources = sorted(str(p) for p in (HERE / "src").rglob("*.java"))
        run("javac", "--release", "8", "-nowarn", "-cp", deps["android-all.jar"], "-d", classes, *sources)
        run("java", "-cp", deps["dx.jar"], "com.android.dx.command.Main", "--dex",
            f"--min-sdk-version={MIN_SDK}", f"--output={tmp / 'classes.dex'}", classes)
        unsigned = tmp / "unsigned.apk"
        with zipfile.ZipFile(unsigned, "w", zipfile.ZIP_DEFLATED) as apk:
            apk.writestr("AndroidManifest.xml", encode_manifest(manifest_tree(version_code, version_name)))
            apk.write(tmp / "classes.dex", "classes.dex")
            apk.write(page, "assets/index.html")
        run("jarsigner", "-keystore", ensure_keystore(keystore), "-storepass", KEY_PASSWORD, "-keypass", KEY_PASSWORD,
            "-sigalg", "SHA256withRSA", "-digestalg", "SHA-256", "-signedjar", out, unsigned, KEY_ALIAS)
    print(f"APK : {out} ({out.stat().st_size / 1e6:.1f} Mo)")
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--page", type=pathlib.Path, default=pathlib.Path("data/medicaments.html"),
                   help="page autonome créée par python -m app.export_static")
    p.add_argument("--out", type=pathlib.Path, default=pathlib.Path("data/officine-sam.apk"))
    p.add_argument("--deps", type=pathlib.Path, default=pathlib.Path("data/android-deps"))
    p.add_argument("--keystore", type=pathlib.Path, default=pathlib.Path("data/android-test.keystore"))
    p.add_argument("--version-code", type=int, default=1)
    p.add_argument("--version-name", default="1.0")
    a = p.parse_args()
    if not a.page.exists():
        sys.exit(f"Page introuvable : {a.page} (créez-la avec python -m app.export_static)")
    build(a.page, a.out, a.deps, a.keystore, a.version_code, a.version_name)
