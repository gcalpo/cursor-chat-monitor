Cursor Conversation Watcher is a simple tool to monitor the AI agent conversations ("chats") in the Cursor IDE for certain prompts that require user intervention but are easily overlooked by a user if Cursor is in a background or on another screen.  This improves on the simple bell sound built into Cursor.

Implement a simple command line solution in Python.

Allow for configuration of notification triggers via a config file. The chat may use different prompts over time so it will be convenient to not go into code to modify the triggers.

This will eventually be cross-platform, but for now focus on using the Mac OS environment. Architecture should make it easy to add Windows or Linux in the future.

User notifications will take the form of an audio alert using the Mac OS "say" command. Voice type should also be configurable based on the condition that triggered user intervention.

CLI shoud allow for background operation (daemon mode) as well as flags to monitor the daemon, run from the prompt, kill the daemon, show diagnostic data, etc.

Cursor IDE is an Electron app, so we should be able to inspect its elements to find the text or buttons.

DO NOT USE OCR even as a fallback.
