# judy
A Discord Bot for the competitive Overwatch team _Dismissed_.

I created this bot to fulfill tedious managerial duties to both make our lives easier and as a fun exercise writing a bot.  Current capabilities:

- Copy schedule in Google Sheets to `#schedule` channel in Discord server
- Include scrim contact for each block
- Randomize avatar daily at scrim time (6PM EST)

The bot utilizes `apscheduler` to implement a scheduler that is compatible with `asyncio`, which is required for Discord bots and their ability to wait for events.

## Scheduling:
For the following Google Sheets schedule and scrim log:
![](https://i.imgur.com/kcMYob5.png)
![](https://i.imgur.com/gpsDYuk.png)

The following Discord message will be sent:
![](https://i.imgur.com/7SpwMFv.png)

### TODO:
- Customizable reminder system depending on type of event in schedule (scrims, matches, VOD reviews, etc.)
- Support for multiple servers
- Make all of the following editable
    - admins
    - channels (`#schedule`, `#commands`, etc.)
    - spreadsheets / sheets (Google)
