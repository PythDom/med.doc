"""Tests de l'encodeur de manifeste Android binaire (AXML) : on le relit avec un petit décodeur indépendant."""
import importlib.util
import pathlib
import struct
import unittest

spec = importlib.util.spec_from_file_location("build_apk", pathlib.Path(__file__).parents[1] / "android" / "build_apk.py")
build_apk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_apk)


def decode(data):
    """Relit un AXML : (chaînes, identifiants d'attributs, [(événement, balise, {attribut: (type, valeur)})])."""
    kind, header, size = struct.unpack_from("<HHI", data, 0)
    assert (kind, header, size) == (0x0003, 8, len(data))
    offset, strings, resource_ids, events = 8, [], [], []
    while offset < len(data):
        kind, header, size = struct.unpack_from("<HHI", data, offset)
        if kind == 0x0001:
            count, _, _, start, _ = struct.unpack_from("<IIIII", data, offset + 8)
            for i in range(count):
                pos = offset + start + struct.unpack_from("<I", data, offset + header + 4 * i)[0]
                length = struct.unpack_from("<H", data, pos)[0]
                strings.append(data[pos + 2:pos + 2 + 2 * length].decode("utf-16-le"))
        elif kind == 0x0180:
            resource_ids = list(struct.unpack_from(f"<{(size - 8) // 4}I", data, offset + 8))
        elif kind == 0x0102:
            _, _, ns, name, attr_start, attr_size, count = struct.unpack_from("<IIIIHHH", data, offset + 8)
            attrs = {}
            for i in range(count):
                a_ns, a_name, raw, _, _, a_type, a_data = struct.unpack_from(
                    "<IIIHBBI", data, offset + 16 + attr_start + i * attr_size)
                attrs[strings[a_name]] = (a_type, strings[a_data] if a_type == 0x03 else a_data)
            events.append(("start", strings[name], attrs))
        elif kind == 0x0103:
            events.append(("end", strings[struct.unpack_from("<I", data, offset + 20)[0]], None))
        offset += size
    return strings, resource_ids, events


class AndroidManifestTest(unittest.TestCase):
    def test_manifest_round_trip(self):
        data = build_apk.encode_manifest(build_apk.manifest_tree(3, "1.2"))
        self.assertEqual(len(data) % 4, 0)
        strings, resource_ids, events = decode(data)
        # Les noms d'attributs android sont en tête du pool, dans l'ordre de la table de ressources.
        self.assertEqual(resource_ids, sorted(resource_ids))
        self.assertEqual([build_apk.ATTR[s] for s in strings[:len(resource_ids)]], resource_ids)
        starts = [(tag, attrs) for kind, tag, attrs in events if kind == "start"]
        self.assertEqual([t for t, _ in starts], ["manifest", "uses-sdk", "uses-permission", "application", "activity",
                                                   "intent-filter", "action", "category"])
        manifest, uses_sdk, _, application, activity = (a for _, a in starts[:5])
        self.assertEqual(manifest["package"], (0x03, "be.meddoc.officine"))
        self.assertEqual(manifest["versionCode"], (0x10, 3))
        self.assertEqual(manifest["versionName"], (0x03, "1.2"))
        self.assertEqual(uses_sdk["targetSdkVersion"], (0x10, 29))
        self.assertEqual(application["label"], (0x03, "Officine SAM"))
        self.assertEqual(activity["exported"], (0x12, 0xFFFFFFFF))
        self.assertEqual(activity["name"], (0x03, "be.meddoc.officine.MainActivity"))
        self.assertEqual(sum(1 for e in events if e[0] == "start"), sum(1 for e in events if e[0] == "end"))


if __name__ == "__main__":
    unittest.main()
