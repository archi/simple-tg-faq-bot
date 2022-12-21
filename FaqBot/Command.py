from FaqBot.Entry import Entry
from telegram import ParseMode

# This class stores everything needed for a single `/command`
class Command:
    cmddir = ""
    keywords = {}
    entries = []

    # Constructor
    def __init__(self, cmddir):
        self.cmddir = cmddir
        self.keywords = {}
        self.entries = []

        # Gather all files from this commands directory, and create FaqBot.Entry objects from them
        for file in cmddir.iterdir():
            e = Entry(file)
            self.entries.append(e)
            for kw in e.keywords:
                if kw in self.keywords:
                    self.keywords[kw].append(e)
                else:
                    self.keywords[kw] = [e]

    # Debug: print some info on this command to the command line
    def printInfo(self):
        print(self.cmddir)
        for kw in self.keywords:
            l = []
            for e in self.keywords[kw]:
                l.append(e.short_title)
            print(" * " + kw + ": " + ", ".join(l))

    # This creates the reply to this command
    def handler(self, update, context):

        # We expect a list of space separated arguments to the command
        # The 0th argument will be the command itself
        kwListRaw = update.message.text.split(" ")

        # This will store the entries we found
        found = []

        # Only got the command, so give the user a list of known keywords OR print the singular entry for this command
        if len(kwListRaw) == 1:
            if len(self.keywords) == 1:
                # this command has a singular entry. just return that
                found.append(self.entries[0])
            else:
                update.message.reply_text("Please give a list of space-separated keywords to find entries matching ALL keywords (logical-and).\nKnown keywords: " + ", ".join(self.keywords))
                return

        # We got at least one keyword to look for
        # The user might have used ',' for separation, we filter those in this loop
        kwList = []
        for x in kwListRaw[1:]:
            # split e.g. "foo, bar" into ["foo", " bar"]
            for y in x.split(","):
                # get rid of excess spaces, e.g. " bar" -> "bar"
                kw = y.replace(" ", "")
                # skip empty strings
                if kw == "":
                    continue
                # we want only unique keywords, skip everything we already had
                if kw in kwList:
                    continue
                kwList.append(kw)

        # Now for each entry, filter those that match ALL keywords
        for e in self.entries:
            match = 1
            for kw in kwList:
                if not kw in e.keywords:
                    # user supplied $kw is not in this entries list:
                    match = 0
                    break

            # all user supplied keywords were in the entries list:
            if match == 1:
                found.append(e)

        # give a message if nothing was found
        if len(found) == 0:
            update.message.reply_text("Nothing found. To get a list of keywords use /" + self.cmddir.name)
            return

        # format the result(s) and return them to the user
        reply = ""
        for e in found:
            reply += "<i><b>" + e.title + "</b></i>\n"
            reply += e.text

        update.message.reply_text(text=reply, parse_mode=ParseMode.HTML)
