A little script that inspects incoming connections on port 80, and looks
for the user making the request. If the user is downloading a file, and
they already started a download in the past 2 minutes, then kill the old
one.

This prevents my upstream caching proxy from flooding my home PC when
users are clicking around previewing files, or Kodi is scanning, causing
it to cache the entire file.
