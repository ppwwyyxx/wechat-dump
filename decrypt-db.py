#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import struct
import argparse
import logging
import shutil
import subprocess
import javaobj
from hashlib import md5
import xml.etree.ElementTree as ET
from collections import defaultdict

logger = logging.getLogger("wechat")
import wechat  # noqa: F401

try:
    from pysqlcipher3 import dbapi2 as sqlite
except ImportError:  # optional for `uin`/`imei` subcommands
    sqlite = None

RES_DIR = "/mnt/sdcard/tencent/MicroMsg"
MM_DIR = "/data/data/com.tencent.mm"
MM_MICROMSG_DIR = f"{MM_DIR}/MicroMsg"

_ADB_ROOT_TRIED = False
_ADB_ROOT_OK = False


def try_adb_root():
    global _ADB_ROOT_TRIED, _ADB_ROOT_OK
    if _ADB_ROOT_TRIED:
        return _ADB_ROOT_OK
    _ADB_ROOT_TRIED = True

    proc = subprocess.run(
        ["adb", "root"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False
    )
    if proc.returncode != 0:
        msg = proc.stdout.decode("utf-8", errors="replace").strip()
        if msg:
            logger.info(f"`adb root` unavailable: {msg}")
        _ADB_ROOT_OK = False
        return False

    _ADB_ROOT_OK = True
    # Restarting adbd can take a moment.
    subprocess.run(
        ["adb", "wait-for-device"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return True


def adb_command(command):
    proc = subprocess.run(
        ["adb", "shell", "su", "-c", command],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if proc.returncode == 0:
        return proc.stdout

    # Some devices don't support `su` but do support `adb root`.
    try_adb_root()
    proc = subprocess.run(
        ["adb", "shell", command],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if proc.returncode == 0:
        return proc.stdout

    msg = proc.stdout.decode("utf-8", errors="replace").strip()
    raise RuntimeError(f"adb command failed: {command!r}: {msg}")


def _parse_shared_prefs_values(xml_bytes, key):
    if not xml_bytes:
        return []
    try:
        root = ET.fromstring(xml_bytes.decode("utf-8", errors="replace"))
    except Exception:
        return []
    values = []
    for elem in root.iter():
        if elem.get("name") != key:
            continue
        val = elem.get("value")
        if val is not None:
            values.append(val)
        elif elem.text:
            values.append(elem.text)
    return values


def _list_userdirs():
    userdirs = set()
    for d in (MM_MICROMSG_DIR, RES_DIR):
        try:
            out = adb_command(f"ls -1 {d} 2>/dev/null || true")
        except Exception:
            continue
        for line in out.decode("utf-8", errors="replace").splitlines():
            line = line.strip().lower()
            if re.fullmatch(r"[0-9a-f]{32}", line):
                userdirs.add(line)
    return userdirs


def _uin_to_userdir(uin: str) -> str:
    return md5(("mm" + uin).encode("ascii")).hexdigest()


def get_uin(userdir_hint=None):
    candidates = defaultdict(set)

    def add_uin(uin, source):
        if uin is None:
            return
        try:
            uin = str(int(str(uin).strip()))
        except Exception:
            return
        if uin == "0":
            return
        candidates[uin].add(source)

    def read_prefs_xml(fname):
        try:
            return adb_command(f"cat {MM_DIR}/shared_prefs/{fname} 2>/dev/null || true")
        except Exception:
            return None

    out = read_prefs_xml("system_config_prefs.xml")
    for uin in _parse_shared_prefs_values(out, "default_uin"):
        add_uin(uin, "system_config_prefs.xml:default_uin")

    out = read_prefs_xml("com.tencent.mm_preferences.xml")
    for uin in _parse_shared_prefs_values(out, "last_login_uin"):
        add_uin(uin, "com.tencent.mm_preferences.xml:last_login_uin")

    out = read_prefs_xml("auth_info_key_prefs.xml")
    for uin in _parse_shared_prefs_values(out, "auth_uin"):
        add_uin(uin, "auth_info_key_prefs.xml:auth_uin")

    try:
        out = adb_command(f"cat {MM_MICROMSG_DIR}/systemInfo.cfg 2>/dev/null || true")
        add_uin(javaobj.loads(out).get(1, 0), "systemInfo.cfg")
    except Exception:
        logger.warning("uin not found in systemInfo.cfg")

    if not candidates:
        logger.warning("No uin found from known sources.")
        return []

    userdirs = _list_userdirs()
    scored = []
    for uin, sources in candidates.items():
        udir = _uin_to_userdir(uin)
        present = udir in userdirs if userdirs else False
        scored.append((present, len(sources), uin, udir, sorted(sources)))

    scored.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
    for present, _, uin, udir, sources in scored:
        suffix = " (match userdir)" if present else ""
        logger.info(f"uin={uin} userdir={udir}{suffix} from {', '.join(sources)}")

    ordered = [uin for _, _, uin, _, _ in scored]
    if userdir_hint:
        userdir_hint = userdir_hint.strip().lower()
        filtered = [uin for uin in ordered if _uin_to_userdir(uin) == userdir_hint]
        if filtered:
            logger.info(f"Filtered uin candidates by userid={userdir_hint}: {filtered}")
            return filtered
        logger.warning(f"No uin matches userid={userdir_hint}. Trying all candidates.")

    if userdirs:
        matched = [uin for uin in ordered if _uin_to_userdir(uin) in userdirs]
        if matched:
            logger.info(f"Uin candidates with matching userdir: {matched}")
            # Prefer matching uin(s) first, but keep the rest as fallback.
            return matched + [uin for uin in ordered if uin not in matched]

    logger.info(f"Possible uin: {ordered}")
    return ordered


def get_imei():
    candidates = defaultdict(set)

    def add_id(device_id, source):
        if device_id is None:
            return
        device_id = str(device_id).strip()
        if not device_id:
            return
        candidates[device_id].add(source)

    class Parcel(object):
        # https://gist.github.com/ktnr74/60ac7bcc2cd17b43f2cb
        def __init__(self, text):
            words = re.findall(br'([0-9a-f]{8})', text.lower())
            if not words:
                raise Exception('Unexpected input!')
            self.data = b''.join([struct.pack('<L', int(x, 16)) for x in words])
            self.resultcode = self.get_int(0)

        def get_int(self, offset=4):
            return int(struct.unpack('<L', self.data[offset:offset+4])[0])

        def get_utf16(self, offset=4):
            slen = self.get_int(offset)
            if slen <= 0:
                return ""
            raw = self.data[offset + 4: offset + 4 + slen * 2]
            return raw.decode('utf-16', errors='replace').strip('\x00').strip()

    for code in (1, 2, 3, 4):
        try:
            out = adb_command(f"service call iphonesubinfo {code}")
            imei = Parcel(out.strip()).get_utf16()
            if imei:
                add_id(imei, f"iphonesubinfo:{code}")
        except Exception:
            continue
    try:
        out = adb_command("dumpsys iphonesubinfo")
        text = out.decode("utf-8", errors="replace")
        for m in re.findall(r"\b[0-9]{14,17}\b", text):
            add_id(m, "dumpsys:iphonesubinfo")
    except Exception:
        pass

    try:
        out = adb_command(f"cat {MM_DIR}/MicroMsg/CompatibleInfo.cfg 2>/dev/null || true")
        # https://gist.github.com/ChiChou/36556fd412a9e3216abecf06e084e4d9
        jobj = javaobj.loads(out)
        imei = jobj.get(258) if hasattr(jobj, "get") else jobj[258]
    except:
        logger.warning("imei not found in CompatibleInfo.cfg")
    else:
        add_id(imei, "CompatibleInfo.cfg:258")
        try:
            items = jobj.items() if hasattr(jobj, "items") else []
        except Exception:
            items = []
        for k, v in items:
            if not isinstance(v, str):
                continue
            v = v.strip()
            if not v or len(v) > 64:
                continue
            if re.fullmatch(r"[0-9A-Za-z]+", v) and re.search(r"\d", v):
                add_id(v, f"CompatibleInfo.cfg:{k}")

    try:
        out = adb_command("settings get secure android_id 2>/dev/null || true")
        android_id = out.decode("utf-8", errors="replace").strip()
        if re.fullmatch(r"[0-9a-fA-F]{16}", android_id):
            add_id(android_id, "android_id")
    except Exception:
        pass

    # Some devices/ROMs may return a dummy value here, but it can be valid on others.
    add_id("1234567890ABCDEF", "dummy:issue-70")  # https://github.com/ppwwyyxx/wechat-dump/issues/70

    if not candidates:
        logger.warning("No device id candidates found.")
        return []

    scored = []
    for device_id, sources in candidates.items():
        scored.append((len(sources), device_id, sorted(sources)))
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    for _, device_id, sources in scored:
        logger.info(f"device_id={device_id} from {', '.join(sources)}")
    return [device_id for _, device_id, _ in scored]


def get_key(imei, uin):
    """
    Args:
        imei, uin: str
    """
    if isinstance(uin, str):
        uin = uin.encode('ascii')
    if isinstance(imei, str):
        imei = imei.encode('ascii')
    a = md5(imei + uin)
    return a.hexdigest()[:7]


def _is_sqlite_database(path):
    try:
        with open(path, "rb") as f:
            return f.read(16).startswith(b"SQLite format 3\x00")
    except Exception:
        return False


def _do_decrypt_sqlcipher_cli(input, output, key, cipher_compatibility=1):
    if shutil.which("sqlcipher") is None:
        raise RuntimeError("Missing dependency: sqlcipher (required for decrypt).")

    out_sql = output.replace("'", "''")
    script = "\n".join(
        [
            ".bail on",
            f"PRAGMA key='{key}';",
            f"PRAGMA cipher_compatibility={int(cipher_compatibility)};",
            "SELECT count(*) FROM sqlite_master;",
            f"ATTACH DATABASE '{out_sql}' AS db KEY '';",
            "SELECT sqlcipher_export('db');",
            "DETACH DATABASE db;",
            ".exit",
            "",
        ]
    )
    proc = subprocess.run(
        ["sqlcipher", input],
        input=script.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if proc.returncode != 0:
        msg = proc.stdout.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"sqlcipher failed: {msg}")
    if not _is_sqlite_database(output):
        msg = proc.stdout.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Decryption produced invalid output: {msg}")


def do_decrypt(input, output, key, cipher_compatibility=1):
    if sqlite is None:
        try:
            _do_decrypt_sqlcipher_cli(
                input, output, key, cipher_compatibility=cipher_compatibility
            )
        except Exception:
            try:
                if os.path.exists(output):
                    os.unlink(output)
            except Exception:
                pass
            raise
        return

    conn = sqlite.connect(input)
    try:
        c = conn.cursor()
        version_str = list(conn.execute("PRAGMA cipher_version"))[0][0]
        version = tuple([int(x) for x in version_str.split(".")[:2]])
        assert version >= (4, 1), "Sqlcipher>=4.1 is required"

        c.execute("PRAGMA key = '" + key + "';")
        # https://github.com/sqlcipher/sqlcipher/commit/e4b66d6cc8a2b7547a32ff2c3ac52f148eba3516
        c.execute(f"PRAGMA cipher_compatibility = {int(cipher_compatibility)};")

        # Validate the key before exporting, to avoid producing partial output files.
        c.execute("SELECT count(*) FROM sqlite_master;")

        out_sql = output.replace("'", "''")
        c.execute(f"ATTACH DATABASE '{out_sql}' AS db KEY '';")
        logger.info(f"Decryption succeeded! Writing database to {output} ...")
        c.execute("SELECT sqlcipher_export('db');")
        c.execute("DETACH DATABASE db;")
    except Exception:
        try:
            if os.path.exists(output):
                os.unlink(output)
        except Exception:
            pass
        raise
    finally:
        try:
            c.close()
        except Exception:
            pass
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('task', choices=['uin', 'imei', 'decrypt'])
    parser.add_argument('--imei', help='overwrite imei')
    parser.add_argument('--uin', help='overwrite uin')
    parser.add_argument('--userid', help='MicroMsg user dir name (32 hex). Filters uin by md5(\"mm\"+uin).')
    parser.add_argument('--input', help='encrypted EnMicroMsg.db')
    parser.add_argument('--output', help='output decrypted db path (default: <input>.decrypted)')
    parser.add_argument('--compat', type=int, action='append',
                        help='sqlcipher cipher_compatibility to try (repeatable; default: 1)')
    args = parser.parse_args()

    if args.task == 'uin':
        get_uin(userdir_hint=args.userid)
    elif args.task == 'imei':
        get_imei()
    elif args.task == 'decrypt':
        if not args.input:
            parser.error("--input is required for decrypt")

        uins = [args.uin] if args.uin else get_uin(userdir_hint=args.userid)
        imeis = [args.imei] if args.imei else get_imei()
        if not uins:
            parser.error("No uin candidates found. Please provide --uin.")
        if not imeis:
            parser.error("No device id candidates found. Please provide --imei.")

        output_file = args.output or (args.input + ".decrypted")
        if os.path.isfile(output_file):
            parser.error(f"Output {output_file} exists!")

        compat_values = args.compat or [1]
        tried = 0
        for uin in uins:
            for imei in imeis:
                key = get_key(imei, uin)
                for compat in compat_values:
                    tried += 1
                    logger.info(
                        f"Trying uin={uin} device_id={imei} key={key} cipher_compatibility={compat} ..."
                    )
                    try:
                        do_decrypt(args.input, output_file, key, cipher_compatibility=compat)
                    except Exception as error:
                        logger.debug(f"Decrypt attempt failed: {error}")
                        continue
                    logger.info(f"Database dumped to {output_file}")
                    sys.exit(0)

        logger.error(f"Failed to decrypt {args.input} after {tried} attempts.")
        logger.error(
            "If you have multiple accounts, try passing --userid (32-hex MicroMsg dir) to filter uin. "
            "Otherwise, provide --uin/--imei manually, or use Frida/password-cracker (see README)."
        )
        sys.exit(1)
