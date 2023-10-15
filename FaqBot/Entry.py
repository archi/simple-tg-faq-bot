import re;
import os;

# This contains a single entry
class Entry:
    # These store the meta-data for the entry; they are set via their respective setters
    title = ""
    short_title = ""
    keywords = []
    text = ""
    file = ""
    img = False
    default = False

    def __eq__(self, other):
        if not hasattr(other, "title"):
            return NotImplemented
        return self.title == other.title

    def __lt__(self, other):
        if not hasattr(other, "title"):
            return NotImplemented
        return self.title < other.title

    # set the keywords from a given string, e.g. "foo, bar, baz"
    def setKeywords(self, kwStr):
        # split on "," for ["foo", " bar", " baz"]
        for s in kwStr.split(","):
            # strip excess whitespaces, and only add unique entries
            s = s.replace(" ", "")
            if not s in self.keywords:
                self.keywords.append(s.lower())

    # set the short title
    def setShortTitle(self, string):
        self.short_title = string

    # set the full title
    def setTitle(self, string):
        self.title = string

    # add an image
    def setImg(self, string):
        self.img = os.path.dirname(self.file) + "/" + string
        print("Img: " + self.img + "\n")

    # validate the entry
    def valid(self):
        return self.title != "" and self.short_title != "" and len(self.keywords) > 0 and self.text != "" and self.file != ""

    # print some debug info
    def printInfo(self):
        print(self.file)
        if self.valid():
            print(" * Valid: true")
        else:
            print(" * Valid: false")
        print(" * Title: " + self.title)
        print(" * Short Title: " + self.short_title)
        print(" * Keywords: " + ", ".join(self.keywords)) # the language designer must have been on drugs
        print(" * Text:\n" + self.text)

    # initialize the entry by parsing the given file
    # the parser is really stupid, so for double definitions the last one wins; except for keywords, which are unionized
    # everything that's wrong will probably be ignored [yes, the "parser" is stupid]
    def __init__(self, file):
        self.file = file
        f = open(file, "r")
        addText = 0
        lineno = 0
        self.keywords = []
        for line in f:
            lineno = lineno + 1

            # after we're done done with everything else, this parses the content after the "text:" line
            if addText == 1:
                self.text += line
                continue

            if line == "" or line == "\n":
                continue

            if (re.match("^\s*#", line)):
                continue

            # split a line "   foo: bar # baz" into a "foo" and "bar # baz"
            m = re.match("^\s*(title|img|short-title|keywords|text|default):\s*(.*)", line)

            # silently ignore any line that does not match
            # TODO better error handling, people might be surprised by this
            if not m:
                print("Ignoring unknown key in {}:{}".format(str(file), lineno))
                continue

            # handle the known fields from the file:
            if m[1] == "keywords":
                if m[2] != "":
                    self.setKeywords(m[2])
            elif m[1] == "short-title":
                self.setShortTitle(m[2])
            elif m[1] == "title":
                self.setTitle(m[2])
            elif m[1] == "text":
                # special case: parse every line after "text:"
                # TODO someone might do a "text: first or only line", handle this
                addText = 1
            elif m[1] == "default":
                if m[2].lower() in ("1", "true", "yes"):
                    self.default = True
            elif m[1] == "img":
                print("img!\n")
                self.setImg(m[2])
            else:
                # this can't really happen for now, since the regex only produces the above cases
                # should probably go into the "if not m:" body
                print("Bad key at " + str(file) + ":" + lineno + "\n")

        if len(self.keywords) == 0:
            print("No keywords for file " + str(file) + "\n");

        return