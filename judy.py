# Jordan Williams
# TheAfroOfDoom - Afro
# 1/5/20
# Managerial Duties for Dismissed

import asyncio, datetime, discord, os, pickle, pprint, random, socket, time, urllib3
import xml.dom.minidom as minidom, xml.etree.ElementTree as ET

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# I'm always an admin
OWNER_ID = 012345678912345678

# NOTE(jordan): DEBUG HERE
DEBUG = False

# Settings
SETTINGS_FILE_NAME = 'settings.xml'

# Custom exceptions
class TriggerError(ValueError):
    """Raised when a trigger for a scheduler job is an invalid value"""
    def __init__(self, trigger, msg = None):
        if msg is None:
            # Default error message
            msg = "A trigger value of \"%s\" is invalid" % trigger
        super(TriggerError, self).__init__(msg)
        self.trigger = trigger

class UpdateTriggerError(TriggerError):
    """Raised when the defined trigger for update() is an invalid value"""
    def __init__(self, trigger):
        VALID_UPDATE_TRIGGERS = [
                                    'cron',
                                    'interval'                                    
                                ]

        super(UpdateTriggerError, self).__init__(
            trigger, msg = "Trigger for update() was \'%s\', must be one of the following:\n%s" % (trigger, VALID_UPDATE_TRIGGERS))

def write_settings(settings):
    # Create file
    fp = open(SETTINGS_FILE_NAME, 'w')
    
    # Write to file
    fp.write(minidom.parseString(ET.tostring(settings.getroot())).toprettyxml())

# NOTE(jordan): Edit these if necessary
def restore_default_settings(prnt = False):
    if(prnt):
        print("File \"settings.xml\" does not exist.  Creating one with default values...")

    # New blank XML object
    root = ET.XML("<settings></settings>")
    settings = ET.ElementTree(root)

    # NOTE(jordan): Privacy/Security
    #   =   =   =   =   =   =   =   =   =   =   =   =   =   =   =   =
    # Access levels:
    #   - public:   Anyone can read the data
    #   - private:  Nobody can read the data
    #   - guild:    Only members of the guild can read the data
    #
    # All children are assumed to inherit it's parent's level of
    # security at a minimum (can be more secure).
    #
    # Assumed <write> attribute is False, child can overwrite to True.
    # Only admins can edit settings (and only in their respective
    # guilds).
    #   =   =   =   =   =   =   =   =   =   =   =   =   =   =   =   =

    # Default settings
    # <Metadata>
    p = ET.SubElement(root, "properties")
    
    # <Guilds>
    g = ET.SubElement(root, "guilds")

    # Dismissed
    dg = ET.SubElement(g, "guild",                      # dg = dismissed_guild
                        attrib = {'access': 'guild'})
    dg.set('id', str(604867951526543363))               # guild ID
    dg.set('name', "Dismissed")

    dg.append(ET.Element("command_prefix", attrib = {'write': "True"}))
    dg.find(".//command_prefix").text = "/"
    channels = ET.SubElement(dg, "channels",
                            attrib = {'write': "True"})

    channels.append(ET.Element("channel",    # SCHEDULE_CHANNEL_ID
                                attrib = {'id': str("ch_id_schedule"), 
                                        'name': "schedule", 'write': "True"}))
    channels.append(ET.Element("channel",     # UPDATES_CHANNEL_ID
                                attrib = {'id': str("ch_id_updates"), 
                                        'name': "updates", 'write': "True"}))
    channels.append(ET.Element("channel",    # COMMANDS_CHANNEL_ID
                                attrib = {'id': str("ch_id_commands"), 
                                        'name': "commands", 'write': "True"}))

    # # <Admins>
    admins = ET.SubElement(dg, "admins", 
                            attrib = {'write': "True"})

    # # <Spreadsheets>
    spreadsheets = ET.SubElement(dg, "spreadsheets", 
                            attrib = {'write': "True"})

    # # Dismissed
    spreadsheet = ET.SubElement(spreadsheets, "spreadsheet")    # dismissed_guild_dismissed_spreadsheet
    spreadsheet.set("id",   # SPREADSHEET_ID
                    'sprdsht_id')
    spreadsheet.set("name", "Dismissed")

    # # # <Sheets>
    sheets = ET.SubElement(spreadsheet, "sheets")   # dismissed_guild_dismissed_spreadsheet_sheets

    # # # Schedule
    sheet = ET.SubElement(sheets, "sheet")  # dismissed_guild_dismissed_spreadsheet_schedule_sheet
    sheet.set("id", 'sht_id_0')  # SCHEDULE_SHEET_ID
    sheet.set("name", 'Schedule')  # SCHEDULE_SHEET_NAME
    sheet.set("range", 'B1:I')     # RANGE_NAME

    # # # Scrim Log
    sheet = ET.SubElement(sheets, "sheet")  # dismissed_guild_dismissed_spreadsheet_scrimlog_sheet
    sheet.set("id", 'sht_id_1')    # SCRIM_LOG_SHEET_ID
    sheet.set("name", 'Scrim Log')  # SCRIM_LOG_SHEET_NAME
    
    # # # # <Columns>
    columns = ET.SubElement(sheet, "columns")
    columns.append(ET.Element("column", attrib = {"name": "teams"}))
    columns.find(".//column[@name='teams']").text = "0"
    columns.append(ET.Element("column", attrib = {"name": "contact"}))
    columns.find(".//column[@name='contact']").text = "2"

    # Write file
    #print(minidom.parseString(ET.tostring(root)).toprettyxml())
    write_settings(settings)
    return(settings)

def guild_setting_to_str(setting):
    s = ""

    if(setting.tag == "command_prefix"):
        s += "`" + setting.text + "`"
    
    elif(setting.tag == "channels"):
        if(len(list(setting)) == 0):
            s += "(None)"

        else:
            for chan in setting:
                s += "#" + chan.get("name") + " `" + chan.get("id") + "`\n"

    elif(setting.tag == "admins"):
        if(len(list(setting)) == 0):
            s += "(None)"

        else:
            for admin in setting:
                s += admin.get("user") + "\n"

    elif(setting.tag == "spreadsheets"):
        if(len(list(setting)) == 0):
            s += "(None)"
        
        else:
            for spreadsheet in setting:
                s += "" + spreadsheet.get("name") + " `" + spreadsheet.get("id") + "`\n"
                sheets = spreadsheet.findall(".//sheet")
                if(len(list(sheets)) == 0):
                    s += "- (None)"

                else:
                    for sheet in sheets:
                        s += "- " + sheet.get("name") + " `" + sheet.get("id") + "`\n"

                        r = sheet.get("range")
                        if(r != None):
                            s += "- - Range: " + r + "\n"

                        cols = sheet.find("./columns")
                        if(cols != None):
                            if(len(list(cols)) != 0):
                                for col in cols:
                                    s += "- - " + col.get("name").title() + " Column: " + col.text + "\n"

                        s += "\n"

    return(s)

# Load settings
try:
    settings = ET.parse(SETTINGS_FILE_NAME)
except FileNotFoundError:
    settings = restore_default_settings(prnt = True)
except ET.ParseError:
    i = ''
    while(i != 'y' and i != 'n'):
        i = input("Error decoding settings file.  Restore defaults? (y/n): ").lower()

    if(i == 'y'):
        settings = restore_default_settings()
    else:
        raise ET.ParseError

# If modifying these scopes, delete the file token.pickle.
GOOGLE_SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# Bot stuff
load_dotenv()
discord_token = os.getenv('DISCORD_TOKEN')
client = discord.Client()

# Import settings
d = settings.find("./guilds/guild")  # First guild in settings (assume is Dismissed for now)
GUILD_ID = d.get("id")
SCHEDULE_CHANNEL_ID = int(d.find("./channels/channel[@name='schedule']").get("id"))

# IDs and ranges
s = d.find("./spreadsheets/spreadsheet[@name='Dismissed']")
SPREADSHEET_ID = s.get("id")
ss = s.find("./sheets/sheet[@name='Schedule']")
SCHEDULE_SHEET_ID = ss.get("id")
SCHEDULE_SHEET_NAME = ss.get("name")
RANGE_NAME = SCHEDULE_SHEET_NAME + "!" + ss.get("range")

ss = s.find("./sheets/sheet[@name='Scrim Log']")
SCRIM_LOG_SHEET_ID = ss.get("id")
SCRIM_LOG_SHEET_NAME = ss.get("name")
SCRIM_LOG_TEAM_COLUMN = ord(ss.find("./columns/column[@name='teams']").text) - ord('A')
SCRIM_LOG_CONTACT_COLUMN = ord(ss.find("./columns/column[@name='contact']").text) - ord('A')

# NOTE(jordan): Scheduled job properties
UPDATE_TRIGGER_TYPE = 'cron'
UPDATE_MISFIRE_GRACE_TIME = 30 * 60                 # 30 minutes => seconds

RANDOMIZE_AVATAR_MISFIRE_GRACE_TIME = 4 * 60 * 60   # 4 hours => seconds

AVATAR_DIR = "/icons/judge_judy/"
AVATAR_URL = "https://cdn.discordapp.com/avatars/<user_id>/<hash>.jpg"
http = urllib3.PoolManager()

# PrettyPrinter
pp = pprint.PrettyPrinter()

# Event scheduler
s = AsyncIOScheduler()

# Event scheduler's trigger for update()
if(UPDATE_TRIGGER_TYPE == 'cron'):
    # FORMAT: https://apscheduler.readthedocs.io/en/v2.1.2/cronschedule.html
    # At certain time formats                                             \/
    UPDATE_TIME = '0'                   # What minute to update on (ex. 2:00:00)

elif(UPDATE_TRIGGER_TYPE == 'interval'):
    # Every <x> amount of time.
    UPDATE_TIME = 30       # (minutes)

else:
    raise UpdateTriggerError(UPDATE_TRIGGER_TYPE)

# NOTE(jordan): Update these for event names to ignore
IGNORE_EVENTS = [
                    "offblock",
                    "holiday",
                    "holidays"
                ]

class Event:
    def __init__(self, name = "", contact = "",
                start = -1, end = -1, notes = [],
                delta = datetime.timedelta(minutes = 30),
                _type = ""):
        self.name = name
        self.contact = contact

        self.start = start
        self.end = end

        self.notes = []
        self.delta = delta
        self.type = _type

    def set_notes(self, notes, split = '\n'):
        self.notes = notes.split(split)

    def __repr__(self):
        return("Event()")

    def __str__(self, note_sep = ', '):
        start_ampm = self.start.strftime('%p').lower()
        end_ampm = self.end.strftime('%p').lower()

        # Fix hour to be 12-hour time and not "0"
        start_hr = str(int(self.start.hour) % 12)
        if(start_hr == "0"):
            start_hr = "12"
        # If minute are 00, only show the hour
        start = start_hr + self.start.strftime(':%M')
        if(self.start.strftime('%M') == "00"):
            start = start_hr

        end_hr = str(int(self.end.hour) % 12)
        if(end_hr == "0"):
            end_hr = "12"
        end = end_hr + self.end.strftime(':%M')
        if(self.end.strftime('%M') == "00"):
            end = end_hr

        # ex. contact = ' (Afro#12419)'
        if(self.contact != ""):
            contact = " (" + self.contact + ")"
        else:
            contact = self.contact

        # If end - start = delta (only 1 cell), only display the
        # starting time (not the range of time).
        if(self.end - self.start == self.delta):
            event_str = "%s%s %s%s" % (start, start_ampm, self.name, contact)
        else:
            # Display start's AM/PM only if it is different from end's
            if(start_ampm == end_ampm):
                start_ampm = ''

            event_str = "%s%s-%s%s %s%s" % (start, start_ampm, end, end_ampm, self.name, contact)

        # Add notes to event_str if they exist
        if(len(self.notes) != 0):
            # Add " | " if event name is not blank
            if(self.name.strip() != ""):
                event_str += " | "

            # Add each note to string with provided separator
            for note in self.notes:
                event_str += note + note_sep

            # Remove hanging note separator
            event_str = event_str[:-len(note_sep)]
            
        return(event_str)

def get_google_creds():
    # Copied from
    # https://developers.google.com/sheets/api/quickstart/python
    
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', GOOGLE_SCOPES)
            creds = flow.run_local_server(port = 0)

        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return(creds)

async def randomize_avatar():
    '''
        Randomize profile picture every day at scrim time (default 6pm EST)
        to one of the pictures inside '/icons/judge_judy'
    '''
    if(DEBUG):
        print("%s: <randomize_avatar()>." % (datetime.datetime.now()))

    url = AVATAR_URL.replace("<user_id>", str(client.user.id)).replace("<hash>", str(client.user.avatar))

    # Current avatar
    current_avatar = http.request('GET', url)
    
    # Randomly choose avatar that is not current avatar
    avatar = random.choice([open(os.getcwd() + AVATAR_DIR + ava, "rb") for ava in os.listdir(os.getcwd() + AVATAR_DIR)
                            if open(os.getcwd() + AVATAR_DIR + ava, "rb").read() != current_avatar.data])

    await client.user.edit(avatar = avatar.read())

async def update_schedule(google_creds):
    '''
        Generate markdown of schedule and see if it has been modified.
        If so, save the new one.
    '''
    if(DEBUG):
        print("%s: <update_schedule()>." % (datetime.datetime.now()))

    # Download sheets from Google Sheets using credentials
    service = build('sheets', 'v4', credentials = google_creds)

    # Call the Sheets API

    # Raw values in 2D format
    values_raw = service.spreadsheets().values().get(spreadsheetId = SPREADSHEET_ID,
                        range = RANGE_NAME, majorDimension = 'COLUMNS').execute()
   
    values = values_raw.get('values', [])  # Columns is major dimension

    if not values:
        print('ERROR: No data found.')

    else:
        # Determine current week
        d = datetime.date.today()
        week_of = d - datetime.timedelta(days = d.weekday())   # Monday of current week

        # Date as string that matches Daygirl's format
        d_str = str(week_of.month) + '/' + week_of.strftime('%d')
        
        # Match Monday to dates in spreadsheet
        # Iterate through second column
        row = 0
        for cell in values[1]:
            # Skip empty cells
            if cell == '':
                row += 1
                continue

            if(d_str == values[1][row].split()[-1]):
                break
            row += 1

        # Save information
        timezone = values[0][row]
        time_start = datetime.datetime.strptime(values[0][row + 1], "%I:%M %p")   # The first time listed in this week's schedule (ex. 2:00 PM)
        time_delta = datetime.datetime.strptime(values[0][row + 2], "%I:%M %p") - time_start  # The span of time a single cell represents

        # Get height of week
        row_max = row + 1
        for cell in values[0][row_max:-1]:
            if(timezone == values[0][row_max + 1]):
                break
            row_max += 1

        # Calculate range of current_week on the sheet
        current_week_range_name =  SCHEDULE_SHEET_NAME + '!C' + str(row + 1) + ':I' + str(row_max + 1)
        # Grab the full data of schedule sheet only of current week
        spreadsheets = service.spreadsheets().get(spreadsheetId = SPREADSHEET_ID,
                                            ranges = current_week_range_name, includeGridData = True).execute()
        for sheet in spreadsheets["sheets"]:
            if(str(sheet["properties"]["sheetId"]) == SCHEDULE_SHEET_ID):
                schedule_sheet = sheet
                break

        # NOTE(jordan): Edit these as we need more information from cells
        # Clean up useless information for readability
        gross_keys =    [
                            "effectiveValue",
                            "userEnteredFormat",
                            "userEnteredValue"
                        ]

        for each_row in schedule_sheet["data"][0]["rowData"]:
            for cell in each_row["values"]:
                for gross in gross_keys:
                    if(gross in cell):
                        del cell[gross]
        
        # Grab merged cells to determine event lengths
        merges = schedule_sheet["merges"]

        start_row = schedule_sheet["data"][0]["startRow"]
        start_col = schedule_sheet["data"][0]["startColumn"]

        schedule = []
        for day in range(7):    # Monday (0) ... Sunday (6)
            schedule.append([]) # Each day has a list of events

        # Iterate through each row
        for row_index, each_row in enumerate(schedule_sheet["data"][0]["rowData"][1:]):
            
            # Iterate through cells in each row
            for day, cell in enumerate(each_row["values"]):
                # Skip blank cells
                if("formattedValue" not in cell and
                    "note" not in cell):
                    continue
                
                # Initialize values
                n = ""
                c = ""
                s = time_start + (row_index * time_delta)
                
                # Calculate how long an event is based on merged cells (3 steps)
                # Default length is 1 cell (30 minutes)
                h = 1
                #   1. Calculate true row and column of current cell relative to entire sheet
                mrow = row_index + start_row + 1
                mcol = day + start_col
                #   2. Select correct merged cells based on starting row and column
                for merge in merges:
                    if(mrow == merge["startRowIndex"] and
                        mcol == merge["startColumnIndex"]):
                        #   2.5. Assert that the merge is only 1 column wide
                        assert (merge["endColumnIndex"] - mcol == 1), "Merged cells at (%d, %d) are more than 1 column wide!" % (mrow, mcol)

                        #   3. Return length of event based on how many rows are merged
                        h = merge["endRowIndex"] - mrow
                        break

                # Stuff for "formattedValue"
                if("formattedValue" in cell):

                    # If event name is one we want to ignore, skip over
                    if(cell["formattedValue"].lower().replace(" ", "") in IGNORE_EVENTS):
                        continue

                    # Add event to day
                    n = cell["formattedValue"].strip()  # Remove leading/trialing whitespace

                    # Grab scrim log sheet
                    # Grab the full data of schedule sheet only of current week
                    scrim_log = service.spreadsheets().get(spreadsheetId = SPREADSHEET_ID, ranges = SCRIM_LOG_SHEET_NAME,
                                                            includeGridData = True).execute()
                    for sheet in scrim_log["sheets"]:
                        if(str(sheet["properties"]["sheetId"]) == SCRIM_LOG_SHEET_ID):
                            scrim_log_sheet = sheet
                            break

                    # Clean up useless information for readability
                    for scrim_log_each_row in scrim_log_sheet["data"][0]["rowData"]:
                        for scrim_log_cell in scrim_log_each_row["values"]:
                            for gross in gross_keys:
                                if(gross in scrim_log_cell):
                                    del scrim_log_cell[gross]

                    # Grab contact
                    # Iterate through rows in the Scrim Log sheet, column "SCRIM_LOG_TEAM_COLUMN"
                    for scrim_log_row_index, scrim_log_row in enumerate(scrim_log_sheet["data"][0]["rowData"]):    

                        scrim_log_cell = scrim_log_row["values"][SCRIM_LOG_TEAM_COLUMN]

                        # Skip blank cells
                        if("formattedValue" not in scrim_log_cell):
                            continue
            
                        # If cell is the event's team
                        if(n.lower() == scrim_log_cell["formattedValue"].strip().lower()):
                            # If contact exists, save it
                            if("formattedValue" in scrim_log_row["values"][SCRIM_LOG_CONTACT_COLUMN]):
                                # Save contact
                                c = scrim_log_row["values"][SCRIM_LOG_CONTACT_COLUMN]["formattedValue"].strip()

                            # Else it does not exist                            

                        # Or if the notes (aliases) are it
                        if("note" in scrim_log_cell):
                            # map(strip, ...)/map(lower, ...) removes leading/trailing whitespace and lowercases all characters
                            if(n.lower() in map(str.lower, map(str.strip, scrim_log_cell["note"].split('\n')))):

                                # Save contact
                                c = scrim_log_row["values"][SCRIM_LOG_CONTACT_COLUMN]["formattedValue"].strip()

                e = Event(name = n, delta = time_delta, contact = c,
                            start = s, end = s + (time_delta * h))

                # Only include notes if event has not been cancelled
                if("cancelled" not in n.lower() and
                    "note" in cell):
                    e.set_notes(cell["note"])

                schedule[day].append(e)

        '''
        for day in schedule:
            for e in day:
                print(e.contact)
        '''

        d = int(week_of.day)
        if(4 <= d <= 20 or 24 <= d <= 30):
            suffix = "th"
        else:
            suffix = ["st", "nd", "rd"][d % 10 - 1]
            
        schedule_str = "**Week of " + week_of.strftime('%b') + ' ' + str(week_of.day) + suffix + "**\n```\n"
        for d in range(7):
            day = datetime.timedelta(days = d) + week_of   # 0 (Monday) .. 6 (Sunday)

            # ex. "Mon 1/06:"
            schedule_str += day.strftime("%a") + " " + str(day.month) + day.strftime("/%d:\n")

            # If there are no events, put "OFF" filler event
            if(len(schedule[d]) == 0):
                schedule_str += "    OFF\n"
            else:   # Otherwise, iterate through the events and add them
                for event in schedule[d]:
                    schedule_str += "    " + str(event) + "\n"
            schedule_str += "\n"

        schedule_str += "```"
        
        # c = #schedule channel
        c = client.get_channel(SCHEDULE_CHANNEL_ID)

        # Compare schedule_str to currently posted schedule
        #   1. Grab ID of last posted message by bot in #schedule
        message_id = -1
        async for m in c.history():
            if(m.author.id == client.user.id and
                m.channel.id == SCHEDULE_CHANNEL_ID):
                message_id = m.id

        # If the bot has posted a message before in #schedule:
        if(message_id != -1):
            try:
                m = await c.fetch_message(message_id)
            except discord.errors.NotFound:
                return
            # Store week that message was posted
            # Ex. "**Week of Jan 6th**..."
            #                ^    ^
            last_message_week_of = datetime.datetime.strptime(m.content[10:15], "%b %d")

            # If week differs from last message's week, delete that message and post a new message
            if(week_of.month != last_message_week_of.month and
                week_of.day != last_message_week_of.day):
                await delete(m)
                await c.send(schedule_str)

            # Else, we're still in the same week so just edit the message
            # (if it differs)
            elif(schedule_str != m.content):
                await m.edit(content = schedule_str)
        
        # Else, the bot has not posted a message before in #schedule,
        # so just post one.
        else:
            await c.send(schedule_str)

async def update(*args):
    '''
        Update:
            - schedule
    '''
    if(DEBUG):
        print("%s: <update()>." % (datetime.datetime.now()))

    # Assert that we are in at least 1 server.
    a0 = len(client.guilds) != 0
    assert a0, "%s is not in any guilds." % (client.user)

    # NOTE(jordan): This assumes we only want Judy for our own team
    #               and don't expand.
    # Assert the only server we're in is Dismissed.
    a1 = len(client.guilds) == 1
    try:
        assert a1, "%s is in a server that is not %s." % (client.user, client.get_guild(604867951526543363).name)
    except AssertionError:
        for g in client.guilds: # List all guilds that are not Dismissed.
            if(g.id != GUILD_ID):
                print("\t%s (%s): %s" % (g.name, g.owner, g.id))
        pass    # Pass so we still have server functionality even though
                # bot is in another server.

    # Update credentials for Google API access.
    google_creds = get_google_creds()

    # Update schedule in #schedule channel based on the Google Sheet.
    await update_schedule(google_creds)

async def edit_settings(msg, *args):

    # Mode parameter provides which alias ran this function
    # ex. '/settings', '/events', '/admins'
    try:
        mode = args[-1]
    except Exception:
        mode = 'settings'   # Default mode if no args are passed

    if(mode == 'settings'):
        # Grab this guild's settings section
        guild_settings = settings.find(".//guild[@id='" + str(msg.guild.id) + "']")

        # Grab guild command prefix
        prefix = guild_settings.find("command_prefix").text

        # If no args, list guild settings
        if(len(args) == 1):

            # Create embed
            embed = discord.Embed(
                color = 6684723,
                title = client.user.name + " Settings",
                description = "Edit a setting using `" + prefix + "settings edit <option>`."
            )

            embed.set_author(name = client.user.name,
                            icon_url = client.user.avatar_url)

            # Start of fields list is writable settings
            for writable_child in guild_settings.findall("./*[@write='True']"):
                # Print writeable children as un-faded
                embed.add_field(
                    name = "**" + writable_child.tag.replace("command_prefix", "prefix").replace("_", " ").replace("-", " ").title() + "**",
                    value = guild_setting_to_str(writable_child)
                )

            # Latter part of fields list is read-only settings
            for readonly_child in guild_settings.findall("./*[@write='False']"):
                # Print read-only children as italicized
                embed.add_field(
                    name = readonly_child.tag.replace("command_prefix", "prefix").replace("_", " ").replace("-", " ").title(),
                    value = "*" + guild_setting_to_str(readonly_child) + "*"
                )

            # Send list of settings embed
            await msg.channel.send(embed = embed)

    return

async def purge_messages(msg, *args):
    # Save certain message properties
    auth_id = msg.author.id
    ch_id = msg.channel.id

    if(len(args) == 1):
        # Delete all messages
        deleted = await msg.channel.purge()
        u = client.get_user(auth_id)
        confirmation = str(len(deleted)) + " messages purged by " + u.mention + "."
        await client.get_channel(ch_id).send(confirmation, delete_after = 30)

async def execute(func, msg, *args):

    done        = "\U00002705"  # White Checkmark w/Green Background
    in_progress = "\U0001F552"  # Clock - 3:00
    failed      = "\U0000274C"  # Red X

    # Runs the provided function with reaction fluff to interact with the user
    await msg.add_reaction(in_progress)
    try:
        await func(msg, args)
    except Exception:
        try:
            await msg.add_reaction(failed)
            await msg.remove_reaction(in_progress, client.user)
        except discord.errors.NotFound: # Required if message was purged by command
            return
    else:
        try:
            await msg.add_reaction(done)
            await msg.remove_reaction(in_progress, client.user)
        except discord.errors.NotFound: # Required if message was purged by command
            return

@client.event
async def on_ready():
    print("%s: %s is ready." % (datetime.datetime.now(), client.user))
    #print("Press 'q' to quit: ")

    '''
        Update every <interval> hours.
    '''
    # Update stored guilds' names
    for guild in settings.find("./guilds"):
        guild.set("name", client.get_guild(int(guild.get("id"))).name)

    # Update once upon ready
    await update()

    # Updates every <UPDATE_TIME> minutes OR at every <UPDATE_TIME>   

    # Start scheduler if it is not already running
    if(not s.running):
        s.start()

@client.event
async def on_disconnect():
    print("%s: %s has disconnected." % (datetime.datetime.now(), client.user))

@client.event
async def on_connect():
    print("%s: %s has connected." % (datetime.datetime.now(), client.user))

@client.event
async def on_resumed():
    print("%s: %s has reconnected." % (datetime.datetime.now(), client.user))

@client.event
async def on_message(msg):

    # Grab this guild's settings section
    guild_settings = settings.find(".//guild[@id='" + str(msg.guild.id) + "']")

    # Grab guild command prefix
    prefix = guild_settings.find("command_prefix").text

    #print([a.get("id") for a in guild_settings.findall(".//admin[@id]")])

    # If msg was in #commands channel and the author was an admin:
    if(str(msg.channel.id) in [ch.get("id") for ch in guild_settings.findall("./channels/channel[@name='commands']")] and
        (msg.author.id == OWNER_ID or str(msg.author.id) in [a.get("id") for a in guild_settings.findall(".//admin[@id]")])):
        
        # If message starts with command prefix
        if(msg.content[0:len(prefix)] == prefix):

            # Strip leading/trailing whitespace
            command = msg.content[len(prefix):].strip().split() # split() by " " for optional **args

            commands =  [
                            "help",
                            "purge",
                            "settings",
                            "update"
                        ]

            # Force update
            if(command[0] in commands):
                # Function the command actually points to
                if("settings" in command[0]):
                    command[0] = command[0].replace("settings", "edit_settings")
                    command.append("settings")  # mode
                elif("purge" in command[1]):
                    command[0] = command[0].replace("purge", "purge_messages")

                # Pass args if there are any
                if(len(command) > 1):
                    await execute(eval(command[0]), msg, command[1:])
                else:
                    await execute(eval(command[0]), msg)

            # Command not defined
            else:
                unknown = "\U00002753"  # Red Question Mark
                await msg.add_reaction(unknown)

# NOTE(jordan): Edit here for how often to update().
if(UPDATE_TRIGGER_TYPE == 'cron'):
    s.add_job(update, 'cron', minute = UPDATE_TIME, misfire_grace_time = UPDATE_MISFIRE_GRACE_TIME)
elif(UPDATE_TRIGGER_TYPE == 'interval'):
    s.add_job(update, 'interval', minutes = UPDATE_TIME, misfire_grace_time = UPDATE_MISFIRE_GRACE_TIME)

# FORMAT: https://apscheduler.readthedocs.io/en/v2.1.2/cronschedule.html
# Default for randomizing profile picture is at 6pm EST (scrim time)
if(DEBUG):
    s.add_job(randomize_avatar, 'interval', minutes = 5)
else:
    s.add_job(randomize_avatar, 'cron', hour = 18, misfire_grace_time = RANDOMIZE_AVATAR_MISFIRE_GRACE_TIME)

try:
    client.run(discord_token)
    
except KeyboardInterrupt:
    pass
except socket.timeout:
    print("Connection timed out at ", datetime.datetime.now)
    pass
