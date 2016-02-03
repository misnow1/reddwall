on run theFile
  tell application "Finder" to set desktop picture to POSIX file theFile
  tell application "System Events"
    set theDesktops to a reference to every desktop
    set picture of item 2 of the theDesktops to POSIX file theFile
  end tell
end run

