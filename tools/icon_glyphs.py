"""VivaldiDark icon glyphs on a 28x28 grid (live area 6..22), every coordinate a multiple of 0.5.

Each glyph is a list of SVG elements; the root <svg> supplies stroke="currentColor", width 1.6, round caps.
"""


def P(d):
    return f'<path d="{d}"/>'


def C(cx, cy, r):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}"/>'


def R(x, y, w, h, rx=1.5):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}"/>'


def DOT(cx, cy, r=1):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="currentColor" stroke="none"/>'


# reusable parts
ENVELOPE = [R(6.5, 8.5, 15, 11), P("m7 9.5 7 5.5 7-5.5")]
PAGE = [P("M9 6.5h6.5l3.5 3.5v11.5H9z"), P("M15.5 6.5V10H19")]
TRASH = [P("M7.5 9.5h13"), P("M11.5 9.5V8a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1v1.5"), P("M9 9.5l.5 11a1.5 1.5 0 0 0 1.5 1.5h6a1.5 1.5 0 0 0 1.5-1.5l.5-11")]
CALENDAR = [R(6.5, 8, 15, 13.5), P("M6.5 12h15"), P("M10.5 6v3.5"), P("M17.5 6v3.5")]
BOX = [R(6.5, 7.5, 15, 4, 1), P("M8 11.5v8.5a1.5 1.5 0 0 0 1.5 1.5h9a1.5 1.5 0 0 0 1.5-1.5v-8.5")]
WINDOW = [R(6.5, 7.5, 15, 13), P("M6.5 11h15")]
OCTAGON = [P("M11 6.5h6l4.5 4.5v6L17 21.5h-6L6.5 17v-6z")]

GLYPHS = {
    # navigation
    "back": [P("M16.5 8.5 11 14l5.5 5.5")],
    "forward": [P("M11.5 8.5 17 14l-5.5 5.5")],
    "rewind": [P("M8 9v10"), P("M15 9l-5 5 5 5"), P("M20.5 9l-5 5 5 5")],
    "fast-forward": [P("M20 9v10"), P("M13 9l5 5-5 5"), P("M7.5 9l5 5-5 5")],
    "reload": [P("M20 14a6 6 0 1 1-2-4.5"), P("M18.5 6.5 18 9.5l3 .5")],
    "stop": [P("M9 9l10 10"), P("M19 9 9 19")],
    "home": [P("M7 13.5 14 7.5l7 6"), P("M9 12v9.5h10V12"), P("M12.5 21.5v-5h3v5")],
    "search": [C(12.5, 12.5, 5), P("m16 16 5 5")],
    "download": [P("M14 6.5v10"), P("m10 12.5 4 4 4-4"), P("M7.5 21h13")],
    "reading-list": [C(9.5, 15.5, 3), C(18.5, 15.5, 3), P("M12.5 15a1.5 1.5 0 0 1 3 0"), P("M6.5 14.5l1.5-5"), P("M21.5 14.5l-1.5-5")],
    "update": [C(14, 14, 7.5), P("M14 18V10"), P("m10.5 13.5 3.5-3.5 3.5 3.5")],
    "extensions": [P("M10 9.5h2.5a2 2 0 1 1 4 0H19v4a2 2 0 1 1 0 4v3.5h-4a2 2 0 1 0-4 0H8V17a2 2 0 1 0 0-4V9.5z")],
    "vpn": [P("M14 6.5 20.5 9v4.5c0 4-2.5 6.5-6.5 8-4-1.5-6.5-4-6.5-8V9z"), C(14, 13.5, 1.5), P("M14 15v2.5")],
    "share": [P("M14 6.5v10"), P("m10.5 10 3.5-3.5 3.5 3.5"), P("M9.5 13H8.5a1 1 0 0 0-1 1v6.5a1 1 0 0 0 1 1h11a1 1 0 0 0 1-1V14a1 1 0 0 0-1-1h-1")],
    # status bar
    "break-mode": [C(14, 14, 7.5), P("M12 11v6"), P("M16 11v6")],
    "mail": ENVELOPE,
    "calendar": CALENDAR + [DOT(10.5, 15.5), DOT(14, 15.5), DOT(17.5, 15.5), DOT(10.5, 18.5), DOT(14, 18.5)],
    "sync": [P("M20.5 12a6.5 6.5 0 0 0-12-2"), P("M8 6.5V10h3.5"), P("M7.5 16a6.5 6.5 0 0 0 12 2"), P("M20 21.5V18h-3.5")],
    "capture": [P("M7 11V8.5A1.5 1.5 0 0 1 8.5 7H11"), P("M17 7h2.5A1.5 1.5 0 0 1 21 8.5V11"), P("M21 17v2.5a1.5 1.5 0 0 1-1.5 1.5H17"), P("M11 21H8.5A1.5 1.5 0 0 1 7 19.5V17"), C(14, 14, 2.5)],
    "tiling": [R(6.5, 6.5, 6.5, 6.5, 1), R(15, 6.5, 6.5, 6.5, 1), R(6.5, 15, 6.5, 6.5, 1), R(15, 15, 6.5, 6.5, 1)],
    "images": [R(6.5, 7.5, 15, 13), C(11, 12, 1.5), P("m6.5 18.5 4.5-4 3.5 3 3-2.5 4 3.5")],
    "auto-hide": [R(6.5, 7.5, 15, 13), P("M6.5 11h2"), P("M11 11h2"), P("M15.5 11h2"), P("M20 11h1.5")],
    "page-actions": [P("M11 9.5 6.5 14l4.5 4.5"), P("M17 9.5l4.5 4.5-4.5 4.5"), P("M15.5 8l-3 12")],
    "clock": [C(14, 14, 7.5), P("M14 10v4.5l3 2")],
    "settings": [C(14, 14, 2.5), P("M19.5 13h2v2h-2l-1 2 1.5 1.5-1.5 1.5-1.5-1.5-2 1v2h-2v-2l-2-1-1.5 1.5L8 18.5 9.5 17l-1-2h-2v-2h2l1-2L8 9.5 9.5 8 11 9.5l2-1v-2h2v2l2 1L18.5 8 20 9.5 18.5 11z")],
    # panels
    "panel-toggle": [R(6.5, 7.5, 15, 13), P("M11.5 7.5v13")],
    "bookmarks": [P("M9.5 7h9v14.5L14 18l-4.5 3.5z")],
    "history": [P("M7.5 14a6.5 6.5 0 1 0 2-4.5"), P("M7 7v3.5h3.5"), P("M14 10.5V14l2.5 2")],
    "notes": PAGE + [P("M11.5 13.5h5"), P("M11.5 16.5h5"), P("M11.5 19.5h3")],
    "windows": [R(9, 6.5, 12.5, 10, 1.5), P("M18.5 19.5v.5a1.5 1.5 0 0 1-1.5 1.5H8a1.5 1.5 0 0 1-1.5-1.5v-7.5A1.5 1.5 0 0 1 8 11h1"), P("M9 9.5h12.5")],
    "translate": [P("M6.5 9.5h8"), P("M10.5 7.5v2"), P("M13 9.5c-.5 3-2.5 5.5-5.5 7"), P("M9 12.5c1 1.5 2.5 3 4.5 4"), P("m14.5 21.5 3.5-8 3.5 8"), P("M15.5 19h5")],
    "tasks": [R(6.5, 7.5, 4, 4, 1), P("M13.5 9.5h8"), P("m7 17 1.5 1.5L11 16"), P("M13.5 17h8")],
    "feeds": [DOT(8.5, 19.5, 1.5), P("M7.5 13.5a7 7 0 0 1 7 7"), P("M7.5 8a12.5 12.5 0 0 1 12.5 12.5")],
    "contacts": [R(6.5, 6.5, 15, 15), C(14, 12, 2.5), P("M9.5 19c.5-2 2.5-3.5 4.5-3.5s4 1.5 4.5 3.5")],
    "sessions": [P("M14 6.5 21.5 10 14 13.5 6.5 10z"), P("m6.5 14 7.5 3.5 7.5-3.5"), P("m6.5 18 7.5 3.5 7.5-3.5")],
    "web-panel": [R(6.5, 6.5, 15, 15), P("M14 10.5v7"), P("M10.5 14h7")],
    # tab bar
    "workspaces": [R(6.5, 11.5, 11, 10), P("M9.5 8.5H19a1.5 1.5 0 0 1 1.5 1.5v8.5"), P("M12.5 5.5H22a1.5 1.5 0 0 1 1.5 1.5v8.5")],
    "new-tab": [P("M14 8v12"), P("M8 14h12")],
    "synced-tabs": [P("M10 19.5h-.5a3.5 3.5 0 0 1-.5-7 5 5 0 0 1 9.5-1.5 4 4 0 0 1 .5 8.5h-1"), P("M14 14.5v7"), P("m11.5 19 2.5 2.5 2.5-2.5")],
    "trash": TRASH,
    "tab": [P("M5.5 20h2.5l1-10a1.5 1.5 0 0 1 1.5-1.5h7a1.5 1.5 0 0 1 1.5 1.5l1 10h2.5")],
    # mail
    "compose": [P("M13 7.5H8.5A1.5 1.5 0 0 0 7 9v10.5A1.5 1.5 0 0 0 8.5 21H19a1.5 1.5 0 0 0 1.5-1.5V15"), P("M19 6.5l2.5 2.5-7 7H12v-2.5z")],
    "undo": [P("M10.5 8.5 7 12l3.5 3.5"), P("M7 12h9a4.5 4.5 0 0 1 0 9h-3.5")],
    "edit": [P("M17.5 7l3.5 3.5L11 20.5H7.5V17z"), P("M15.5 9l3.5 3.5")],
    "reply": [P("M11.5 9.5 7 14l4.5 4.5"), P("M7 14h8.5a5.5 5.5 0 0 1 5.5 5.5v1")],
    "reply-all": [P("M12 9.5 7.5 14l4.5 4.5"), P("M9 9.5 4.5 14 9 18.5"), P("M7.5 14h8.5a5.5 5.5 0 0 1 5.5 5.5v1")],
    "mail-forward": [P("M16.5 9.5 21 14l-4.5 4.5"), P("M21 14h-8.5A5.5 5.5 0 0 0 7 19.5v1")],
    "mail-read": [P("M6.5 12 14 7l7.5 5v8a1.5 1.5 0 0 1-1.5 1.5H8A1.5 1.5 0 0 1 6.5 20z"), P("m7 12.5 7 5 7-5")],
    "mail-unread": [R(6.5, 8.5, 15, 11), P("m7 9.5 7 5.5 7-5.5"), DOT(20.5, 8.5, 2.5)],
    "flag": [P("M8.5 21.5v-15"), P("M8.5 7.5h10l-2 3.5 2 3.5h-10")],
    "label": [P("M6.5 8v5.5l8.5 8.5 7-7-8.5-8.5H8A1.5 1.5 0 0 0 6.5 8z"), DOT(10.5, 10.5, 1.5)],
    "move": [P("M6.5 10V8.5A1.5 1.5 0 0 1 8 7h4l2 2h6a1.5 1.5 0 0 1 1.5 1.5v9A1.5 1.5 0 0 1 20 21H8a1.5 1.5 0 0 1-1.5-1.5V17"), P("M5.5 13.5h9"), P("m12 11 2.5 2.5L12 16")],
    "spam": OCTAGON + [P("M14 10v5"), DOT(14, 18, 1)],
    "not-spam": OCTAGON + [P("m10.5 14 2.5 2.5 4.5-4.5")],
    "archive": BOX + [P("M12 15h4")],
    "unarchive": BOX + [P("M14 19.5v-5.5"), P("m11.5 16.5 2.5-2.5 2.5 2.5")],
    "unmark-trash": TRASH + [P("M14 19.5v-6"), P("m11.5 16 2.5-2.5 2.5 2.5")],
    "quick-response": [P("M7 8.5A1.5 1.5 0 0 1 8.5 7h11A1.5 1.5 0 0 1 21 8.5v8a1.5 1.5 0 0 1-1.5 1.5H13l-4 3.5V18h-.5A1.5 1.5 0 0 1 7 16.5z"), P("M10.5 11h7"), P("M10.5 14h4.5")],
    "render-html": PAGE + [R(11.5, 12.5, 5, 4, 1), P("M11.5 19.5h5")],
    "render-text": PAGE + [P("M11.5 13h5"), P("M11.5 16h5"), P("M11.5 19h5")],
    "threads": [P("M7.5 8.5h13"), P("M11 14h9.5"), P("M14.5 19.5h6"), P("M7.5 8.5V14h3.5"), P("M11 14v5.5h3.5")],
    "threads-flat": [P("M7.5 8.5h13"), P("M7.5 14h13"), P("M7.5 19.5h13")],
    "layout": [R(6.5, 7.5, 15, 13), P("M12 7.5v13"), P("M12 14h9.5")],
    "send": [P("M21.5 6.5 6.5 12.5l6 2.5 2.5 6z"), P("m12.5 15 4-4")],
    "attach": [P("M19.5 13.5 13 20a4 4 0 0 1-5.5-5.5L15 7a2.5 2.5 0 0 1 3.5 3.5L11.5 17.5a1 1 0 0 1-1.5-1.5l6-6")],
    "headers": [R(6.5, 7.5, 15, 13), P("M6.5 11.5h15"), P("M9.5 14.5h9"), P("M9.5 17.5h6")],
    "discard": PAGE + [P("m11.5 13.5 5 5"), P("m16.5 13.5-5 5")],
    "format-rich": [P("M8.5 8h11"), P("M14 8v10"), P("M8.5 21.5h11")],
    "format-text": [P("M7.5 9h13"), P("M7.5 14h13"), P("M7.5 19h8")],
    "undock": WINDOW + [P("M16 20.5h-.5"), P("M14 17.5l5-5"), P("M15.5 12.5H19V16")],
    "dock": WINDOW + [P("M18.5 13 14 17.5"), P("M14 14v3.5h3.5")],
}

BUTTONS = {
    "PanelToggle": "panel-toggle", "Back": "back", "Forward": "forward", "Rewind": "rewind",
    "FastForward": "fast-forward", "Reload": "reload", "Stop": "stop", "Home": "home", "SearchField": "search",
    "DownloadButton": "download", "ReadingList": "reading-list", "UpdateButton": "update", "Extensions": "extensions",
    "VPNButton": "vpn", "SharePageButton": "share",
    "BreakMode": "break-mode", "MailStatus": "mail", "CalendarStatus": "calendar", "SyncStatus": "sync",
    "CaptureImages": "capture", "TilingToggle": "tiling", "ImagesToggle": "images", "AutoHideToggle": "auto-hide",
    "PageActions": "page-actions", "Clock": "clock", "Settings": "settings",
    "PanelBookmarks": "bookmarks", "PanelReadingList": "reading-list", "PanelDownloads": "download",
    "PanelHistory": "history", "PanelNotes": "notes", "PanelWindow": "windows", "PanelTranslate": "translate",
    "PanelMail": "mail", "PanelCalendar": "calendar", "PanelTasks": "tasks", "PanelFeeds": "feeds",
    "PanelContacts": "contacts", "PanelSession": "sessions", "PanelWeb": "web-panel",
    "WorkspaceButton": "workspaces", "NewTab": "new-tab", "SyncedTabs": "synced-tabs", "TabsTrash": "trash",
    "TabButton": "tab",
    "MailBack": "back", "MailForward": "forward", "MailReload": "reload", "MailCompose": "compose", "MailUndo": "undo",
    "MailMsgEdit": "edit", "MailMsgReply": "reply", "MailMsgReplyToAll": "reply-all", "MailMsgForward": "mail-forward",
    "MailMsgStatusRead": "mail-read", "MailMsgStatusUnread": "mail-unread", "MailMsgFlag": "flag",
    "MailMsgLabel": "label", "MailMsgMove": "move", "MailMsgSpam": "spam", "MailMsgSpamRestore": "not-spam",
    "MailMsgArchive": "archive", "MailMsgArchiveRestore": "unarchive", "MailMsgTrash": "trash",
    "MailMsgTrashRestore": "unmark-trash", "MailViewQuickResponse": "quick-response",
    "MailRenderingMethod": "render-html", "MailRenderingMethodText": "render-text", "MailViewThreading": "threads",
    "MailViewThreadingFlat": "threads-flat", "MailViewLayout": "layout", "MailMsgSend": "send",
    "MailMsgAttach": "attach", "MailMsgShowHeaders": "headers", "MailMsgDiscard": "discard",
    "MailComposeFormat": "format-rich", "MailComposeFormatText": "format-text", "MailComposerUndock": "undock",
    "MailComposerDock": "dock",
}
