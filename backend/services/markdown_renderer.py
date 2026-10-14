import markdown
from bs4 import BeautifulSoup


class MarkdownRenderer:
    @staticmethod
    def parse(markdown_text: str):
        html = markdown.markdown(markdown_text)

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        blocks = []

        for element in soup.children:

            if element.name == "h1":
                blocks.append(
                    (
                        "h1",
                        element.get_text(),
                    )
                )

            elif element.name == "h2":
                blocks.append(
                    (
                        "h2",
                        element.get_text(),
                    )
                )

            elif element.name == "p":
                blocks.append(
                    (
                        "p",
                        element.get_text(),
                    )
                )

            elif element.name == "ul":

                for li in element.find_all("li"):

                    blocks.append(
                        (
                            "li",
                            li.get_text(),
                        )
                    )

        return blocks