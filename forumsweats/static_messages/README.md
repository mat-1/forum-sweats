This file contains the contents of channels, it's updated automatically whenever files are changed.

Putting a `---` on a line will signify a separate message.
Putting text inside a comment `<!-- -->` won't make it show up in the actual Discord message. If the comment is on its own line, the line is removed.

Technical pseudocode of how this works:
```py
messages = get_static_messages_in_folder()
# send/update all the messages
for static_message_channel_id, static_message_contents in messages:
	# split the big message into several up to 2000 characters
	new_messages = split_discord_message(static_message_contents)
	# get the old ids of the message
	old_message_ids = await db.get_existing_static_message_ids(static_message_channel_id)
	# get the old content of the message
	old_messages = []
	for old_message_id in old_message_ids:
		old_messages.append((await get_message(old_message_id)).content)
	# if they're the same, we don't need to do anything
	if new_messages == old_messages:
		continue
	# delete the old messages
	for old_message_id in old_message_ids:
		await delete_message(old_message_id)
	
	# send the new messages
	new_message_ids = []
	for new_message in new_messages:
		new_message_ids.append((await send_message(static_message_channel_id, new_message).id)
```
