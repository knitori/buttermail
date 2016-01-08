"""
Things:
x Attachments, multipart (text/html + text/plain)
- errors-to und co für headerkrams (forgot what this was)
- html-emails, show images from attachment/related
x pgp signatures (uses gnupg)
- pgp encryption
- s/mime
"""

import os
import smtplib
import platform
from contextlib import closing

from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart

import magic

from .utils import make_quoted_printable, mails_to_string
from .pgp import sign_message
from .types import Html, Text


def send(message, subject, sender, recipients, *,
         attachments=None, cc=None, bcc=None, reply_to=None,
         signature_uid=None, signature_passphrase=None,
         host='localhost', port=25, ssl=False, html_body=None,
         body_as_html=False, encoding='UTF-8'):

    if isinstance(message, str):
        message = Text(message, encoding)

    msg = build_message(message, subject, sender, recipients,
                        attachments=attachments, cc=cc, reply_to=reply_to,
                        encoding=encoding,
                        signature_uid=signature_uid,
                        signature_passphrase=signature_passphrase)

    if ssl:
        smtp = smtplib.SMTP_SSL(host=host, port=port)
    else:
        smtp = smtplib.SMTP(host=host, port=port)

    all_recipients = recipients[:]
    all_recipients.extend(cc if cc is not None else [])
    all_recipients.extend(bcc if bcc is not None else [])
    smtp.sendmail(sender, all_recipients, msg.as_bytes())


def build_message(
        message, subject, sender, recipients, *,
        cc=None, attachments=None, reply_to=None, encoding='UTF-8',
        signature_uid=None, signature_passphrase=None):

    # create the textual message
    if isinstance(message, Html):
        htmlmsg = MIMEText(message.body, 'html', message.encoding)
        make_quoted_printable(htmlmsg)

        if message.plain_version:
            textmsg = MIMEMultipart('alternative')
            plainmsg = MIMEText(message.plain_version,
                                'plain', message.encoding)
            make_quoted_printable(plainmsg)
            textmsg.attach(htmlmsg)
            textmsg.attach(plainmsg)
        else:
            textmsg = htmlmsg
    else:
        textmsg = MIMEText(message.body, 'plain', message.encoding)
        make_quoted_printable(textmsg)

    # add attachments if necessary
    if attachments:
        msg = MIMEMultipart()
        msg.attach(textmsg)

        if attachments:
            for attachment in build_attachments(attachments):
                msg.attach(attachment)
    else:
        msg = textmsg

    # sign message
    if signature_uid:
        msg = sign_message(msg, default_key=signature_uid,
                           passphrase=signature_passphrase)

    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = mails_to_string(recipients)
    if cc:
        msg['Cc'] = mails_to_string(cc)

    if reply_to:
        msg['Reply-To'] = reply_to

    uname = platform.uname()
    msg['X-Mailer'] = 'Buttermail v0.1 (Python {}; {}-{})'.format(
        platform.python_version(), uname.machine, uname.system.lower()
    )

    return msg


def build_attachments(attachments):
    for attachment in attachments:
        if hasattr(attachment, 'read'):
            fileobject = attachment
        else:
            fileobject = open(attachment, 'rb')
        with closing(fileobject) as f:
            buf = f.read(1024)

            mime_type = magic.from_buffer(buf, mime=True).decode('ascii')
            if '/' in mime_type:
                maintype, subtype = mime_type.split('/', 1)
            else:
                maintype, subtype = 'application', 'octet-stream'

            f.seek(0)
            if maintype == 'image':
                msg = MIMEImage(f.read(), _subtype=subtype)
            elif maintype == 'audio':
                msg = MIMEAudio(f.read(), _subtype=subtype)
            elif maintype == 'application' and subtype != 'octet-stream':
                msg = MIMEApplication(f.read(), _subtype=subtype)
            else:
                msg = MIMEApplication(f.read())
            msg['Content-Disposition'] = 'attachment; filename="{}"'\
                .format(os.path.basename(f.name))
            yield msg
