# Lint Protocol, v1 draft

Lint connects a code editor to linter plugins. The editor starts a plugin as
a subprocess and exchanges JSON-RPC 2.0 messages with it over stdin and
stdout, one message per line.

## 1. Lifecycle

- The editor sends `initialize` with `{"editor": "<name>/<version>"}`. The
  plugin replies with `{"plugin": "<name>/<version>"}`.
- The editor sends `shutdown` before it closes the plugin's stdin.

## 2. Documents

- The editor sends `open` when the user opens a document:
  `{"method": "open", "params": {"document": "src/main.go", "text": "package main\n..."}}`.
- The editor sends `change` with the document's full new `text` after each
  edit, and `close` when the document is closed.

## 3. Diagnostics

- The plugin sends `diagnostics` notifications:

  ```json
  {"method": "diagnostics", "params": {"document": "src/main.go", "items": [
    {"start": 12, "end": 18, "severity": "warning", "message": "unused variable", "code": "W001"}
  ]}}
  ```

- Each notification replaces all earlier diagnostics for that document.
