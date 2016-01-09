
# Buttermail library

## Example usages

### Gmail, attachment, signature

```python

import buttermail
from buttermail.types import Markdown
import getpass
import sys
import textwrap


def main():
    # fake-factory for sample texts installed.
    from faker import Factory

    fake = Factory.create('de_DE')

    message = '''Hi {name1},\n\n{text}\n\nGreetings\n{name2}\n'''.format(
        name1=fake.name(),
        name2=fake.name(),
        text=textwrap.fill(fake.text(), 75),
    )

    message = Markdown(message)

    buttermail.send(
        message,
        subject='Sample Message',
        sender='example@gmail.com',
        recipients=['email@example.com'],

        # reply_to='private@example.org',
        # cc=['email2@example.com'],
        # bcc=['customercare@nsa.gov']
        attachments=['sample.jpg'],
        signature_uid=sys.argv[1],
        signature_passphrase=getpass.getpass('Enter Passphrase: '),
        host='smtp.gmail.com',
        port=465,
        ssl=True,
        smtp_user='example@gmail.com',
        smtp_password='your gmail password',
    )


if __name__ == '__main__':
    main()
```
