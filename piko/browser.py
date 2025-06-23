import os
import threading
from time import sleep
from urllib.parse import parse_qs, quote, urljoin, urlparse

import requests as requests
import simpleeval

import piko.adom


class Browser:
    def __init__(self, initialURL: str):
        self.document = piko.adom.Document(self)
        self.URL = initialURL
        self.loading = True
        self.context = {}
        self.debugHistory = "Debugger: Press Alt+K to close.\n"
        self.debugMode = False
        self.cursor_index = -1
        self.scroll = 0
        self.document.focus = -1  # Initialize focus to -1 (no focus)
        self.load_thread = None

    def start_load(self):
        if not self.loading:
            return
        if self.load_thread and self.load_thread.is_alive():
            return

        self.load_thread = threading.Thread(target=self._load_url)
        self.load_thread.daemon = True
        self.load_thread.start()

    def _load_url(self):
        self.evaluator = (
            self.createEvaluator()
        )  # reset evaluator before new page is loaded
        self.document = loadFromURL(self.URL, self)
        sleep(0.2)  # Add a small delay to ensure loading indicator is visible
        self.loading = False
        self.scroll = 0
        self.document.call_document_action("start", {})
        self.document.call_document_action("redirect", {})
        # Reset focus state
        self.document.unfocus()
        self.cursor_index = -1
        # Only auto-focus if there are inputs and autofocus is enabled
        if self.document.hasInputs:
            self.document.focus_next()
            focused = self.document.get_focused_element()
            if focused and focused.getAttribute("autofocus") == "no":
                self.document.unfocus()

    def createEvaluator(self):
        evaluator = simpleeval.EvalWithCompoundTypes()
        evaluator.functions = simpleeval.DEFAULT_FUNCTIONS
        evaluator.functions.update(self.script_functions())
        return evaluator

    # returns if the browser should exit
    def open_link(self, URL: str) -> bool:
        if URL != "piko://exit":
            if URL.startswith("piko://") and not self.URL.startswith("piko://"):
                self.document = piko.adom.Document(self)
                self.document.elements.append(
                    piko.adom.createTextElement(
                        "Can not open piko:// links. Only Piko can open these links."
                    )
                )
            else:
                # Handle relative paths by resolving them against the current URL
                if not URL.startswith(("http://", "https://", "piko://")):
                    # Resolve relative URL against current URL
                    self.URL = urljoin(self.URL, URL)
                else:
                    self.URL = URL
                self.loading = True
            return False
        else:
            return True

    def var(self, name: str, value):
        self.debug(name + ": " + value)
        self.context[name] = value

    def getvar(self, name: str):
        if name in self.context:
            return self.context[name]
        else:
            return "None"

    def setvalue(self, name: str, value: str):
        for element in self.document.elements:
            found = element.find_element_by_id(name)
            if found:
                found.value = value
                break

    def encode(self, text: str):
        return quote(text)

    def geturlparam(self, param: str):
        """Extract a URL parameter from the current URL."""
        try:
            parsed = urlparse(self.URL)
            params = parse_qs(parsed.query)
            return params.get(param, [None])[0]
        except Exception:
            return None

    def debug(self, text: str):
        self.debugHistory += text + "\n"

    def action(self, name: str):
        self.document.call_action(name, {})

    def script_functions(self):
        return {
            "visit": self.open_link,
            "getvar": self.getvar,
            "var": self.var,
            "action": self.action,
            "encode": self.encode,
            "debug": self.debug,
            "geturlparam": self.geturlparam,
            "setvalue": self.setvalue,
        }

    def get_global_variables(self):
        return {
            "BROWSER_URL": self.URL,
            "BROWSER_HOST": urlparse(self.URL).netloc,
            "BROWSER_PATH": urlparse(self.URL).path,
            "BROWSER_QUERY": urlparse(self.URL).query,
            "BROWSER_FRAGMENT": urlparse(self.URL).fragment,
            "BROWSER_SCHEME": urlparse(self.URL).scheme,
            "BROWSER_USERNAME": urlparse(self.URL).username,
            "BROWSER_PASSWORD": urlparse(self.URL).password,
        }

    def focus_url_bar(self) -> None:
        """Focus the URL bar and set cursor position."""
        self.document.unfocus()
        self.document.focus = -2
        self.cursor_index = len(self.URL)

    def unfocus_url_bar(self) -> None:
        """Unfocus the URL bar."""
        self.document.unfocus()
        self.document.focus = -1
        self.cursor_index = -1


"""
piko:// -> files in the ./local/ folder of the piko project
file:// -> files on the user's computer
http:// & https:// -> files to curl from the internet
"""


def loadFromURL(URL: str, browser: Browser):
    if URL == "":
        return piko.adom.Document(browser).with_message("Error: URL is empty")
    protocol = None
    protocols = ["piko://", "http://", "https://"]
    for p in protocols:
        if URL.startswith(p):
            protocol = p
            break
    if protocol is None:
        return piko.adom.Document(browser).with_message(
            f"Error: Could not determine URL protocol `{URL}`"
        )
    elif protocol == "piko://":
        file_path = (
            os.path.dirname(os.path.realpath(__file__))
            + "/local/"
            + URL[len("piko://") :]
            + ".xml"
        )
        try:
            stream = open(file_path)
            res = stream.read()
            stream.close()
            return piko.adom.xml2doc(res, browser)
        except FileNotFoundError:
            return piko.adom.Document(browser).with_message(
                f"Could not load `{file_path}`"
            )
    elif protocol == "https://" or protocol == "http://":
        sleep(0.1)
        try:
            return makeRequest(browser, URL)
        except Exception as e:
            browser.debug(str(e))
            return piko.adom.Document(browser).with_message(
                "Could not load URL. \n" + str(e)
            )


def makeRequest(browser: Browser, url: str):
    try:
        page = requests.get(url, headers={"User-Agent": "Piko"}).text
        return piko.adom.xml2doc(page, browser)
    except Exception as e:
        browser.debug(str(e))
        return piko.adom.Document(browser).with_message(
            "Could not load URL. \n" + str(e)
        )
