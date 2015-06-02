# lets-encrypt-icecast
A lets-encrypt plugin for Icecast2.

To use it with lets-encrypt:
* download the lets-encrypt preview client at https://github.com/letsencrypt/lets-encrypt-preview
* put icecast.py in `lets-encrypt-preview/letsencrypt/plugins/icecast2/`
* edit `lets-encrypt-preview/setup.py` and add an entry to entry_points at the bottom like `"icecast2 = letsencrypt.plugins.icecast2.icecast2:IcecastInstaller"`

Finally check that the plugin is recognized by running `letsencrypt --help`. You should see the icecast2 plugin and its command line options.

Start lets-encrypt to obtain a certificate however you like for example with `letsencrypt --authenticator standalone -d mydomain auth`.
Let lets-encrypt run the icecast plugin for example with `letsencrypt --installer icecast2 install` and dont forget icecast2's command line options.

To run correctly the plugin needs the location of the icecast configuration file e.g. icecast.xml. This file will be changed to enable ssl so you better let it run on a copy.
The plugin additionally creates a new file containing both the public (certificate) and private key, per default in the current directory, and creates a new ssl enabled socket in the icecast configuration.
