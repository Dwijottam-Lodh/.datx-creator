import os
import json
import glob
import stat

def xor_encrypt_decrypt(data_bytes, password_bytes):
    return bytes([b ^ password_bytes[i % len(password_bytes)] for i, b in enumerate(data_bytes)])

def set_readonly(filename):
    os.chmod(filename, stat.S_IREAD)

def remove_readonly(filename):
    os.chmod(filename, stat.S_IWRITE)

def list_datx_files():
    files = glob.glob("*.datx")
    if not files:
        print("No .datx files found.")
    else:
        print("Available .datx files:")
        for f in files:
            print(f"  - {f}")

def create_file():
    filename = input("Enter filename to create (with .datx): ").strip()
    if os.path.exists(filename):
        print(f"Error: File '{filename}' already exists.")
        return

    data = {}

    print("Enter key-value pairs. To import a .datx file as value, enter the key then type 'import:<filename.datx>' as value.")
    print("Enter '</>' as key to finish.")
    while True:
        key = input("Key: ").strip()
        if key == "</>":
            break
        val = input("Value: ").strip()

        if val.startswith("import:"):
            import_file = val[7:].strip()
            if not os.path.exists(import_file):
                print(f"Error: Import file '{import_file}' not found. Skipping this key.")
                continue
            imported_json = load_plain_file(import_file)
            if imported_json is None:
                print(f"Error: Could not load '{import_file}'. Skipping this key.")
                continue
            data[key] = imported_json
        else:
            try:
                data[key] = json.loads(val)
            except json.JSONDecodeError:
                data[key] = val

    json_str = json.dumps(data, indent=2)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(json_str)

    set_readonly(filename)
    print(f"Plain file '{filename}' created successfully (not encrypted). Use 'encrypt' command to encrypt it later.")

def load_plain_file(filename):
    if not os.path.exists(filename):
        print(f"File '{filename}' does not exist.")
        return None
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Failed to load plain file '{filename}': {e}")
        return None

def encrypt_file():
    filename = input("Enter filename to encrypt (must exist, plain .datx): ").strip()
    if not os.path.exists(filename):
        print(f"File '{filename}' not found.")
        return

    password = input("Enter password to encrypt the file: ").strip()
    remove_readonly(filename)
    data = load_plain_file(filename)
    if data is None:
        return

    json_str = json.dumps(data)
    encrypted = xor_encrypt_decrypt(json_str.encode("utf-8"), password.encode("utf-8"))

    with open(filename, "wb") as f:
        f.write(encrypted)

    set_readonly(filename)
    print(f"File '{filename}' encrypted successfully.")

def decrypt_file():
    filename = input("Enter filename to decrypt (encrypted .datx): ").strip()
    if not os.path.exists(filename):
        print(f"File '{filename}' not found.")
        return

    password = input("Enter password to decrypt the file: ").strip()
    try:
        with open(filename, "rb") as f:
            encrypted = f.read()
        decrypted = xor_encrypt_decrypt(encrypted, password.encode("utf-8"))
        json_str = decrypted.decode("utf-8")
        data = json.loads(json_str)
    except Exception as e:
        print(f"Failed to decrypt or parse file '{filename}': {e}")
        return

    print(f"Decrypted data from '{filename}':\n{json.dumps(data, indent=2)}")

def search_in_file():
    filename = input("Enter filename to search (with .datx): ").strip()
    if not os.path.exists(filename):
        print(f"File '{filename}' not found.")
        return

    # Determine if file is encrypted or plain by trying to load as JSON first
    data = load_plain_file(filename)
    if data is not None:
        # Plain JSON loaded successfully
        print("Loaded as plain JSON.")
    else:
        # Try decrypt
        password = input("Could not load as plain JSON. Enter password to decrypt: ").strip()
        try:
            with open(filename, "rb") as f:
                encrypted = f.read()
            decrypted = xor_encrypt_decrypt(encrypted, password.encode("utf-8"))
            json_str = decrypted.decode("utf-8")
            data = json.loads(json_str)
            print("File decrypted successfully.")
        except Exception as e:
            print(f"Failed to decrypt or parse file: {e}")
            return

    key = input("Enter key to search for: ").strip()

    def search_key(data_dict, search_key):
        if search_key in data_dict:
            return data_dict[search_key]
        for v in data_dict.values():
            if isinstance(v, dict):
                found = search_key(v, search_key)
                if found is not None:
                    return found
        return None

    val = search_key(data, key)
    if val is None:
        print(f"Key '{key}' not found in '{filename}'.")
    else:
        print(f"Value for '{key}': {json.dumps(val, indent=2)}")

def delete_file():
    filename = input("Enter filename to delete (with .datx): ").strip()
    if not os.path.exists(filename):
        print(f"File '{filename}' not found.")
        return
    try:
        remove_readonly(filename)
        os.remove(filename)
        print(f"File '{filename}' deleted successfully.")
    except Exception as e:
        print(f"Error deleting file '{filename}': {e}")

def overwrite_file():
    filename = input("Enter filename to overwrite (with .datx): ").strip()
    if not os.path.exists(filename):
        print(f"File '{filename}' not found.")
        return

    password = input("Enter password to encrypt after overwriting (leave blank for plain file): ").strip()
    remove_readonly(filename)

    data = {}

    print("Enter key-value pairs to overwrite. To import a .datx file as value, enter the key then type 'import:<filename.datx>' as value.")
    print("Enter '</>' as key to finish.")
    while True:
        key = input("Key: ").strip()
        if key == "</>":
            break
        val = input("Value: ").strip()

        if val.startswith("import:"):
            import_file = val[7:].strip()
            if not os.path.exists(import_file):
                print(f"Error: Import file '{import_file}' not found. Skipping this key.")
                continue
            # Try decrypt import file if encrypted else load plain
            imported_json = load_plain_file(import_file)
            if imported_json is None:
                pw = input(f"File '{import_file}' may be encrypted. Enter password to decrypt: ").strip()
                try:
                    with open(import_file, "rb") as f:
                        encrypted = f.read()
                    decrypted = xor_encrypt_decrypt(encrypted, pw.encode("utf-8"))
                    imported_json = json.loads(decrypted.decode("utf-8"))
                except Exception as e:
                    print(f"Failed to load '{import_file}': {e}")
                    continue
            data[key] = imported_json
        else:
            try:
                data[key] = json.loads(val)
            except json.JSONDecodeError:
                data[key] = val

    json_str = json.dumps(data, indent=2)
    if password:
        encrypted = xor_encrypt_decrypt(json_str.encode("utf-8"), password.encode("utf-8"))
        with open(filename, "wb") as f:
            f.write(encrypted)
        set_readonly(filename)
        print(f"File '{filename}' overwritten and encrypted successfully.")
    else:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(json_str)
        set_readonly(filename)
        print(f"File '{filename}' overwritten successfully (plain JSON).")

def main():
    print("Welcome to the .datx file manager.")
    while True:
        print("\nCommands: create, encrypt, decrypt, load, search, del/delete, overwrite, files, exit")
        cmd = input("Enter command: ").strip().lower()
        if cmd == "create":
            create_file()
        elif cmd == "encrypt":
            encrypt_file()
        elif cmd == "decrypt":
            decrypt_file()
        elif cmd == "load":
            filename = input("Enter filename to load (with .datx): ").strip()
            data = load_plain_file(filename)
            if data is not None:
                print(f"Plain JSON data in '{filename}':\n{json.dumps(data, indent=2)}")
            else:
                print("File is likely encrypted, use 'decrypt' command instead.")
        elif cmd in ("del", "delete"):
            delete_file()
        elif cmd == "search":
            search_in_file()
        elif cmd == "overwrite":
            overwrite_file()
        elif cmd == "files":
            list_datx_files()
        elif cmd == "exit":
            print("Goodbye!")
            break
        else:
            print("Unknown command.")

if __name__ == "__main__":
    main()
