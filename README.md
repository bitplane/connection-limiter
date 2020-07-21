# What is it?

A little script that limits the number of downloads that a user
can initiate via a transparent proxy to my home machine. If the user is
downloading a file, and they already started a download in the past 2 
minutes, then kill the old download.

This prevents my upstream caching proxy from flooding my home PC when
users are clicking around previewing files, or Kodi is scanning, causing
it to cache the entire file when they only really peeked at the first few
bytes of it.

# How does it work?

It uses `tcpdump` to intercept inbound TCP connections that start with
`GET`, pulls out the HTTP headers and the user name, then uses `tcpkill`
to kill old connections for that user.

# That's horrible

Yes it is. Cool though isn't it? And it was a lot more fun than trying to
write an `nginx` plugin.
