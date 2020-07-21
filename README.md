# What is it?

A little script that inspects incoming connections on port 80, and looks
for the user making the request. If the user is downloading a file, and
they already started a download in the past 2 minutes, then kill the old
one.

This prevents my upstream caching proxy from flooding my home PC when
users are clicking around previewing files, or Kodi is scanning, causing
it to cache the entire file.

# How does it work?

It uses `tcpdump` to intercept inbound TCP connections that start with
`GET`, pulls out the HTTP headers and the user name, then uses `tcpkill`
to kill old connections for that user.

# That's horrible

Yes it is. Cool though isn't it? And it was a lot more fun than trying to
write an `nginx` plugin.
