
from email.mime.multipart import MIMEMultipart
from email.message import Message

import os
import gnupg


def sign_message(msg: Message, default_key=None,
                 passphrase=None, homedir=None):
    textmsg = msg.as_string().replace('\n', '\r\n')
    if homedir is None:
        homebase = os.environ.get('HOME')
        if homebase:
            homedir = os.path.join(homebase, '.gnupg')
    gpg = gnupg.GPG(homedir=homedir)
    signature = str(
        gpg.sign(textmsg, default_key=default_key,
                 detach=True, clearsign=False,
                 passphrase=passphrase)
    )
    sigmsg = Message()
    sigmsg['Content-Type'] = 'application/pgp-signature; name="signature.asc"'
    sigmsg['Content-Description'] = 'OpenPGP digital signature'
    sigmsg.set_payload(signature)

    outer = MIMEMultipart(_subtype="signed", micalg="pgp-sha256",
                          protocol="application/pgp-signature")

    outer.attach(msg)
    outer.attach(sigmsg)
    return outer
