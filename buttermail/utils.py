
from email.message import Message
from quopri import encodestring as _encodestring


def mails_to_string(arg):
    if isinstance(arg, (bytes, str)):
        return arg
    return ', '.join(arg)


def make_quoted_printable(message: Message):
    """
    Default is base64, so this can be used to
    change a Message to quo-pri.
    """
    payload = message.get_payload(decode=True)
    encdata = _encodestring(payload, quotetabs=True)
    message.set_payload(encdata)
    message.replace_header('Content-Transfer-Encoding', 'quoted-printable')
