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

from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart

import magic

from .utils import make_quoted_printable, mails_to_string
from .pgp import sign_message
from .types import Html, Text


def send(message, subject, sender, recipients, *, encoding='UTF-8',
         attachments=None, cc=None, bcc=None, reply_to=None,
         signature_uid=None, signature_passphrase=None,
         host='localhost', port=25, ssl=False,
         smtp_user=None, smtp_password=None, headers=None):
    """Send an email.

    :param str | Text message:
    :param str subject:
    :param str sender:
    :param list[str] recipients:
    :param str encoding:
    :param list[str | io.BufferedIOBase] attachments:
    :param list[str] cc:
    :param list[str] bcc:
    :param str reply_to:
    :param str signature_uid:
    :param str signature_passphrase:
    :param str host:
    :param int port:
    :param bool ssl:
    :param str smtp_user:
    :param str smtp_password:
    :param dict[str, str] headers: Additional custom headers
    """

    if isinstance(message, str):
        message = Text(message, encoding)

    msg = build_message(message, subject, sender, recipients,
                        encoding=encoding,
                        attachments=attachments, cc=cc, reply_to=reply_to,
                        signature_uid=signature_uid,
                        signature_passphrase=signature_passphrase,
                        headers=headers)

    if ssl:
        smtp = smtplib.SMTP_SSL(host=host, port=port)
    else:
        smtp = smtplib.SMTP(host=host, port=port)

    if smtp_user and smtp_password:
        smtp.login(smtp_user, smtp_password)

    all_recipients = recipients[:]
    all_recipients.extend(cc if cc is not None else [])
    all_recipients.extend(bcc if bcc is not None else [])
    print(msg.as_string())
    # smtp.sendmail(sender, all_recipients, msg.as_bytes())


def build_message(
        message, subject, sender, recipients, *, encoding='UTF-8',
        cc=None, attachments=None, reply_to=None,
        signature_uid=None, signature_passphrase=None, headers=None):

    # create the textual message
    if isinstance(message, Html):
        htmlmsg = MIMEText(message.body, 'html', message.encoding or encoding)
        make_quoted_printable(htmlmsg)

        if message.plain_version:
            textmsg = MIMEMultipart('alternative')
            plainmsg = MIMEText(message.plain_version,
                                'plain', message.encoding or encoding)
            make_quoted_printable(plainmsg)
            textmsg.attach(htmlmsg)
            textmsg.attach(plainmsg)
        else:
            textmsg = htmlmsg
    else:
        textmsg = MIMEText(message.body, 'plain',
                           message.encoding or encoding)
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

    # Note: there might be cases when multiple headers with the same key
    # are necessary.
    for key, value in headers.items():
        if key in msg:
            msg.replace_header(key, value)
        else:
            msg[key] = value

    return msg


def _get_attachment(f):
    f.seek(0)
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
    return msg


def build_attachments(attachments):
    """Create email.mime objects from attachments list.

    :param list attachments: can be a list of file objects or filenames.
    """
    for attachment in attachments:
        if hasattr(attachment, 'read'):
            # don't close passed file objects
            yield _get_attachment(attachment)
        else:
            with open(attachment, 'rb') as f:
                yield _get_attachment(f)
