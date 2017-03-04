# lets-encrypt-icecast
A lets-encrypt plugin for Icecast.

This plugin is currently not functional and out of date due to changes with letsencrypt (now certbot). I dont believe it is much work to update it but Im not sure when I am going to get around to it.

To use it with lets-encrypt:
* download the lets-encrypt client at https://github.com/letsencrypt/letsencrypt and set it up
* In the letsencrypt folder run `./venv/bin/python path/to/lets-encrypt-icecast/setup.py develop`
* put icecast.py in the letsencrypt folder

Finally check that the plugin is recognized by running `letsencrypt --help all`. You should see the icecast_installer plugin and its command line options.

Start lets-encrypt to obtain a certificate however you like for example with `letsencrypt --authenticator standalone -d mydomain auth`.
Let lets-encrypt run the icecast plugin for example with `letsencrypt -t -i letsencrypt-icecast:icecast_installer run`
or `letsencrypt -t -i letsencrypt-icecast:icecast_installer --letsencrypt-icecast:icecast_installer-configuration_file /path/to/icecast.xml install --cert-path /etc/letsencrypt/certs/0000_csr-letsencrypt.pem --key-path /etc/letsencrypt/keys/0000_key-letsencrypt.pem` and dont forget the plugin's command line options.
The plugin creates a new file containing both the public (also known as certificate) and private key, per default in the current directory, and creates a new ssl enabled socket in the icecast configuration. MAKE SURE you set the permissions of the created key file correctly so only the user running icecast can access it as it CONTAINS YOUR PRIVATE KEY.
