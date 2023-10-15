from FaqBot.Entry import Entry
from telegram.constants import ParseMode
import re

# This class stores everything needed for a single `/command`
class Command:
    cmddir = ""
    keywords = {}
    entries = []
    default = None

    # Constructor
    def __init__(self, cmddir):
        self.cmddir = cmddir
        self.keywords = {}
        self.entries = []
        self.default = None

        # Gather all files from this commands directory, and create FaqBot.Entry objects from them
        for file in cmddir.iterdir():
            if not file.match('*.txt'):
                print("Not loading " + str(file) + "\n");
                continue

            e = Entry(file)
            self.entries.append(e)
            for kw in e.keywords:
                if kw in self.keywords:
                    self.keywords[kw].append(e)
                else:
                    self.keywords[kw] = [e]

            # Allow defining a default reply that's returned on '/cmd':
            if e.default:
                if (self.default == None):
                    self.default = e
                else:
                    # TODO better warning (which command, which entries?)
                    print("Warning: Multiple defaults!")


    # Debug: print some info on this command to the command line
    def printInfo(self):
        print(self.cmddir)
        for kw in self.keywords:
            l = []
            for e in self.keywords[kw]:
                l.append(e.short_title)
            print(" * " + kw + ": " + ", ".join(l))

    def findEntries(self, kwListRaw):
        # Only got the command, so give the user a list of known keywords OR print the singular entry for this command
        if len(kwListRaw) == 1:
            if self.default != None:
                return [self.default]
            elif len(self.keywords) == 1:
                # this command has a singular entry. just return that
                return self.entries
            else:
                return None

        # We got at least one keyword to look for
        # The user might have used ',' for separation, we filter those in this loop
        kwList = []
        for x in kwListRaw[1:]:
            # split e.g. "foo, bar" into ["foo", " bar"]
            for y in x.split(","):
                # harmonize to lower case and get rid of excess spaces, e.g. " bar" -> "bar"
                kw = y.lower().replace(" ", "")
                # skip empty strings
                if kw == "":
                    continue
                # we want only unique keywords, skip everything we already had
                if kw in kwList:
                    continue
                kwList.append(kw)

        # Now for each entry, filter those that match ALL keywords
        found = []
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

        return found

    # This creates the reply to this command
    async def handler(self, update, context):
        # We expect a list of space separated arguments to the command
        # The 0th argument will be the command itself
        search_list = update.message.text.split(" ")
        found = self.findEntries(search_list)

        # found did produce an error:
        if found is None:
            await update.message.reply_text("Please give a list of space-separated keywords to find entries matching ALL keywords (logical-and).\nKnown keywords: " + ", ".join(sorted(self.keywords)))
            return

        # give a message if nothing was found
        if len(found) == 0:
            await update.message.reply_text("Nothing found. To get a list of keywords use /" + self.cmddir.name)
            return
        
        if len(found) > 3:
            # it's possible there are no keywords to narrow the search: 
            if await self.replyKeywords(update, found, search_list):
                return
        
        await self.replyFound(update, found)

    # try to reply with a list of keywords to narrow the search, return True if replied
    # if there are not enough keywords to narrow the search, return False
    async def replyKeywords(self, update, found, search_list):
        reply = "Got " + str(len(found)) + " results, please narrow the search by adding more keywords: "
        kwlist = []
        for e in found:
            for k in e.keywords:
                if not k in kwlist and not k in search_list:
                    kwlist.append(k)
        
        if len(kwlist) < len(kwlist) - 2 or len(kwlist) <= 2:
            return False

        first = True
        kwlist.sort()
        for k in kwlist:
            if not first:
                reply += ", "
            reply += k
            first = False

        await update.message.reply_text(text=reply, parse_mode=ParseMode.HTML)
        return True

    async def replyFound(self, update, found):
        # format the result(s) and return them to the user
        reply = ""
        if len(found) > 1:
            reply = "Keyword has " + str(len(found)) + " matches:\n\n"
        first = True
        img = False
        found.sort()
        for e in found:
            if not first:
                reply += "\n-------------------------\n\n"
            reply += "<i><b>" + e.title + "</b></i>\n"
            reply += e.text
            first = False
            if e.img and not img:
                img = e.img

        if len(found) == 1 and img:
            await update.message.reply_photo(photo=img, caption=reply, parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text(text=reply, parse_mode=ParseMode.HTML)
