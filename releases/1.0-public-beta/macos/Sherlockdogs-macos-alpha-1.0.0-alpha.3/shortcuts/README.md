# Sherlockdogs iOS Shortcut Entry

## Core

This folder contains the user-facing iOS Shortcut entry for Sherlockdogs.

| File | Purpose |
|---|---|
| `Send-to-Sherlockdogs-Inbox.shortcut` | Importable shortcut seed. It appears in the iOS share sheet and saves shared content to a user-selected Sherlockdogs Inbox folder. |
| `README.md` | Release and tester instructions for the shortcut entry. |

## Current Test Entry

`Send-to-Sherlockdogs-Inbox.shortcut` is the current beta seed:

```text
Any app share sheet
-> Send to Sherlockdogs
-> Save File
-> user chooses Sherlockdogs Inbox
-> desktop Sherlockdogs processes the synced file
```

This proves the public user flow: the user receives a shortcut file/link from Sherlockdogs instead of building the shortcut from scratch.

## Public Link Status

The final public-beta entry should be an iCloud Shortcuts link:

```text
https://www.icloud.com/shortcuts/<id>
```

Apple requires the shortcut to be shared through Shortcuts/iCloud to create this public install link. The local CLI signing command was tested, but `shortcuts sign` is killed by the system on this machine, so the package currently ships the importable seed file rather than a public iCloud link.

## How To Produce The Public Link

1. Open `Send-to-Sherlockdogs-Inbox.shortcut` on an iPhone or Mac logged into iCloud.
2. Add it to Shortcuts.
3. Open the shortcut in Shortcuts.
4. Tap or click Share.
5. Choose Copy iCloud Link.
6. Put the generated link into release notes and public docs.

After that, public users only need to tap the iCloud link and choose Add Shortcut.

## Beta Caveat

The seed shortcut asks where to save. For the polished public link, preconfigure or document the Inbox choice clearly:

- iCloud users: `iCloud Drive/Sherlockdogs/Inbox`
- Nutstore users: the synced local Nutstore Inbox folder, or the WebDAV variant described in `IOS_SHORTCUTS_GUIDE.md`
- Other users: any folder synced to their desktop and selected in Sherlockdogs
