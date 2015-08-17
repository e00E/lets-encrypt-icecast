# lets-encrypt-icecast
A lets-encrypt plugin for Icecast.

To use it with lets-encrypt:
* download the lets-encrypt client at https://github.com/letsencrypt/letsencrypt and set it up
* In the letsencrypt folder run `./venv/bin/python path/to/lets-encrypt-icecast/setup.py develop`
* put icecast.py in the letsencrypt folder

Finally check that the plugin is recognized by running `letsencrypt --help all`. You should see the icecast_installer plugin and its command line options.

Start lets-encrypt to obtain a certificate however you like for example with `letsencrypt --authenticator standalone -d mydomain auth`.
Let lets-encrypt run the icecast plugin for example with `letsencrypt --installer icecast_installer install` and dont forget the plugin's command line options.

To run correctly the plugin needs the location of the icecast configuration file e.g. icecast.xml. This file will be changed to enable ssl so you better let it run on a copy.
The plugin additionally creates a new file containing both the public (also known as certificate) and private key, per default in the current directory, and creates a new ssl enabled socket in the icecast configuration. MAKE SURE you set the permissions of the created key file correctly so only the user running icecast can access it as it CONTAINS YOUR PRIVATE KEY.
