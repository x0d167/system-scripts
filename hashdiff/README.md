---

````markdown
# hashdiff

A CLI tool for detecting and inspecting drift between files or directories using content hashing. Designed for personal config management, dotfile integrity checks, or any use case where detecting subtle file changes matters.

---

## 🔍 Features

- **Compare** any two files or directories using SHA-256 hashing
- **Detect** added, removed, or modified files in a directory
- **Optional line-by-line diffs** for text files (using `difflib`)
- **Color-coded output** for quick visual parsing
- **Custom ignore rules** for files or directories
- **Smart skip for non-text files** in diffs

---

## 🧪 Usage

```bash
python hashdiff.py <source> <target> [options]
````

* `<source>`: Path to the source file or directory
* `<target>`: Path to the target file or directory

### 📌 Options

| Option            | Description                                               |
| ----------------- | --------------------------------------------------------- |
| `-v`, `--verbose` | Show file-by-file differences (new, deleted, changed)     |
| `-d`, `--diff`    | Show line-by-line diff for modified text files            |
| `-i`, `--ignore`  | Extra file or directory names to ignore (space-separated) |

---

## 🧾 Examples

Compare two dotfile directories with detailed output and inline diffs:

```bash
python hashdiff.py ~/.dotfiles ~/archive/.dotfiles -v -d
```

Ignore additional noisy files or folders:

```bash
python hashdiff.py ~/project ~/backup/project -i .DS_Store __pycache__ node_modules
```

Compare two individual files:

```bash
python hashdiff.py config.yaml backup/config.yaml
```

---

## ⚙️ Internals

* Uses `hashlib.sha256` for consistent, secure content comparison
* Recursively hashes directories, including relative file paths
* Unified diff output generated via Python’s `difflib`
* Output color provided by `colorama` (with auto-reset)

---

## 🛠️ Future Ideas

* Support for `.hashdiffignore` files
* TUI enhancements via `rich` or `textual`
* JSON or HTML output formats
* Git integration (compare vs HEAD or main)

---

## ✅ Why Use This?

When you want to *know* if something changed — not just guess.

Whether you're tracking dotfiles, backups, or config directories, `hashdiff` is a fast, readable, and reliable way to spot even the tiniest change.

---

```

Let me know when you're ready to start on the Config Status Dashboard or want to track ideas for a future suite of CLI tools!
```

