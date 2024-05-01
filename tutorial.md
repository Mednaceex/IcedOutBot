# Tutorial on the IcedOutBot for the 3P League
We are excited to present our new moderation tool for the rest of the 3P League — the IcedOutBot!
From now on, it will set your matches up automatically, which should make the process faster and
reduce the likelihood of a human error. That being said, please learn how to use this feature.
## Sending picks
Whenever your match is announced, you'll need to submit your picks. Run **/pick** command for
every match you have in the current week. Upon completing one pick, the bot will tell you whether
you have other matches this week that you haven't picked maps for yet.

If your picks have been vetoed by your opponent, you will be notified in a DM. Run **/pick** again and pick
your backup map. Note that the bot commands currently work only within the Iced Out Server.

## Checking picks (MODS ONLY)
Server moderators have the access to **/whopicked** command. Upon running it, you'll get a list
of matches in every tier scheduled for this week. For every match you'll also see which players
picked their maps and which are yet to do so. Please note that the bot doesn't automatically tell
players to make their picks, so use the information provided by the command
to remind people by yourselves.

## Setting up matches (OWNER ONLY)
The last two commands are only available to the 3P League's owner @icy3p.
After a week ends, please update the current week value by running **/changeweek** command
(for example, **/changeweek 7** when the 7th week starts).
To announce matches for the week simply write them in **@Player1 vs @Player2** format in the
channel related to the tier in which the match is supposed to be played. You can have other
symbols in the message, just make sure to have exactly 2 pings in a single line and a word "vs" in
order for the bot to register the match. You can have multiple matches announced in one message.
Example:

*And we have a 3 person round robin this week!*

*The legendary matchup: <@719953889029259308> 🐐 vs <@605488675135946895> <:mindblown:1081199314711355453>*

*<@719953889029259308> vs <@699706359846928425>*

*<@605488675135946895> vs <@699706359846928425>*

If you made a mistake setting up the matches, you can reset a certain tier or all tiers
at once. For this run **/resetmatches** command and select the needed option. After that you can
announce the matches in that tier again.

## Things to remember
1. Please allow DMs in your profile, otherwise you won't get a notification in case your picks get vetoed! 
2. Due to certain issues with the hosting, you might get an "app not responding" message after
using a command. Simply run the command again if it happens.
3. Please don't submit picks between <t:1692005400:t> and <t:1692007200:t>, these are the
maintenance hours so the bot might be down and handle your input incorrectly.
4. If you're not a mod, the only command available to you is **/pick**. If you believe there is
something wrong, like an incorrectly announced match, please contact the league moderators.
5. This is the first week since the release of the feature. Even though it has been rigorously tested,
there might still be glitches and errors. Please check your match to see if there are any errors
like an incorrect pick or a map vetoed by you. If you believe the bot didn't set up your match
correctly, please let me know as soon as possible. I apologize in advance for any inconvenience
that this may cause. Thank you!
