
from forumsweats import db, setuptour
from forumsweats.commandparser import Context
import string
import secrets

name = 'getcode'

async def run(message: Context):
    author = message.author
    author_instance = await db.get_place_user_by_id(author.id)
    
    if author_instance:
        code = author_instance['access_code']
        try:
            await message.author.send(f'Looks like you already have a code, if you forgot it here you go: ||{code}||')
        except:
            pass
        return
    
    activity_bobux = await db.get_activity_bobux(author.id)
    if activity_bobux < 100:
        await message.send('You need at least 100 Bobux to get a code.')
        return
    
    name: str = await setuptour.quick_prompt(
        message,
        prompt_message='Enter your name you want to use for the website',
        invalid_message='Invalid name',
        check=setuptour.check_content,
    )

    if name is None:
        return
    if len(name) > 20:
        await message.send('Name too long. Try again')
        return
    if len(name) < 3:
        await message.send('Name too short. Try again')
        return
    # generate a random string
    access_code = ''.join(secrets.choice(string.ascii_letters + string.digits) for i in range(16))

    await db.create_access_code(author.id, name, access_code)

    try:
        await author.send(f'Heres your code: ||{access_code}||')
    except:
        await message.send('Something went wrong.')