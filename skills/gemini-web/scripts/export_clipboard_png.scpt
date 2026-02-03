-- Export clipboard PNG (from "Copy image" in Gemini) to a file.
-- Usage:
--   osascript skills/gemini-web/scripts/export_clipboard_png.scpt /Users/kimi/Downloads/out.png

on run argv
	if (count of argv) < 1 then error "Missing output path"
	set outPosix to item 1 of argv
	set outPath to POSIX file outPosix
	set theData to the clipboard as «class PNGf»
	set f to open for access outPath with write permission
	set eof of f to 0
	write theData to f
	close access f
	return outPosix
end run
