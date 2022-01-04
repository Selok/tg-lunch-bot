import os
import json

from telegram.utils.types import ODVInput
from tg_ops.bot import Bot
from telegram.update import Update
from telegram.ext import CallbackContext
from config import ENROLL_DIR

def add_me(instance: Bot, update: Update, context: CallbackContext):
    jsonFile = os.path.join(
        ENROLL_DIR,
        f"{update.message.chat_id}.json"
    )
    name = f"{update.message.from_user.full_name}"
    user_id = update.message.from_user.id
    
    enrolled = {}
    invited = set()
    if os.path.isfile(jsonFile):
        with open(jsonFile) as f:
            enrolled = json.load(f)
            if 'invited' in enrolled:
                invited = set(enrolled['invited'])
    
    # cache user info
    user_info = {}
    if 'user_info' in enrolled:
        user_info = enrolled['user_info']        
    user_info[user_id] = {
        'name': name
    }
    enrolled['user_info'] = user_info

    # update invited list 
    update_user = (user_id in invited)
    invited.add(user_id)
    enrolled['invited'] = list(invited)

    with open(jsonFile, "w") as f:
        f.write(json.dumps(enrolled))

    if update_user:
        update.message.reply_text(f"[{name}](tg://user?id={user_id}) already in the invite list\.", parse_mode='MarkdownV2')
    else:
        update.message.reply_text(f"[{name}](tg://user?id={user_id}) added to invite list\.", parse_mode='MarkdownV2')

def remove_me(instance: Bot, update: Update, context: CallbackContext):
    jsonFile = os.path.join(
        ENROLL_DIR,
        f"{update.message.chat_id}.json"
    )
    name = f"{update.message.from_user.full_name}"
    user_id = update.message.from_user.id
    
    enrolled = {}
    invited = set()
    if not os.path.isfile(jsonFile):
        return

    with open(jsonFile) as f:
        enrolled = json.load(f)
        if 'invited' in enrolled:
            invited = set(enrolled['invited'])
    
    # remove cached user info
    if 'user_info' in enrolled:
        user_info = enrolled['user_info']
        if user_id in user_info:
            del user_info[user_id]

    # update invited list 
    update_user = (user_id in invited)
    invited.remove(user_id)
    enrolled['invited'] = list(invited)

    with open(jsonFile, "w") as f:
        f.write(json.dumps(enrolled))

    if update_user:
        update.message.reply_text(f"[{name}](tg://user?id={user_id}) removed from the invite list\.", parse_mode='MarkdownV2')
    else:
        update.message.reply_text(f"[{name}](tg://user?id={user_id}) is not in the invite list\.", parse_mode='MarkdownV2')
