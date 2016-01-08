
class Text:

    def __init__(self, body, encoding='UTF-8'):
        self.body = body
        self.encoding = encoding


class Html(Text):
    plain_version = None


class Markdown(Html):
    _template = '''<html>
    <head></head>
    <body>
        {markup}
    </body>
    </html>'''

    def __init__(self, body, encoding='UTF-8'):
        self.plain_version = body
        import CommonMark
        html = CommonMark.commonmark(body)
        html = self._template.format(markup=html)
        super().__init__(html, encoding)
