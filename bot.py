from transformers import AutoModelForCausalLM, AutoTokenizer
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    filters,
    CallbackContext,
    AIORateLimiter,
    MessageHandler,
    CommandHandler
)
import logging
from db import Database
import torch

db = Database()

checkpoint = "Kirili4ik/ruDialoGpt3-medium-finetuned-telegram"
tokenizer =  AutoTokenizer.from_pretrained(checkpoint)
model = AutoModelForCausalLM.from_pretrained(checkpoint)

checkpoint = torch.load('model/ruDialoGpt3_Dostoevsky.pt', map_location='cpu')
model.load_state_dict(checkpoint['model_state_dict'])

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)



async def start(update: Update, context: CallbackContext):
    await register_user(update, context)
    await update.message.reply_text('К Вашим услугам...')

def store_request(message, response):
    db.add_request(message, response)

async def register_user(update, context):
    _id = update.message.from_user.id
    username = update.message.from_user.username
    first_name = update.message.from_user.first_name
    last_name = update.message.from_user.last_name

    if db.check_user_exists(_id):
        return

    db.add_user(_id, username, first_name, last_name)



def make_response(_id, message):
    dialog_context = db.get_dialog_context(_id)
    dialog_history_ids = convert_dialog_context(dialog_context, message)
    input_len = dialog_history_ids.shape[-1]
    dialog_history_ids = model.generate(
        dialog_history_ids,
        num_return_sequences=1,                   
        max_length=512,
        no_repeat_ngram_size=3,
        do_sample=True,
        top_k=50,
        top_p=0.9,
        temperature = 0.6,                         
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.pad_token_id,
    )
    response = tokenizer.decode(dialog_history_ids[:, input_len:][0], skip_special_tokens=True)
    save_dialog_context(dialog_history_ids)
    return response

def save_dialog_context(dialog_history_ids): 
    dialog_context = ','.join(str(_id) for _id in dialog_history_ids)
    db.add_dialog_context(dialog_context)

async def delete_dialog_context_in_db(update: Update, context: CallbackContext):
    _id = update.message.from_user.id
    db.delete_dialog_context(_id)
    await update.message.reply_text('The chat history is cleared!')

async def message_handle(update: Update, context: CallbackContext):
    message = update.message.text
    _id = update.message.from_user.id
    response = make_response(_id, message)
    store_request(message, response)
    await update.message.reply_text(response)


def get_length(text: str, tokenizer):
    tokens_count = len(tokenizer.encode(text))
    if tokens_count <= 15:
        len_param = '1'
    elif tokens_count <= 50:
        len_param = '2'
    elif tokens_count <= 256:
        len_param = '3'
    else:
        len_param = '-'
    return len_param                     

def convert_dialog_context(dialog_context, message, next_len = 2):
    if dialog_context == '':
        dialog_history_ids = torch.zeros((1, 0), dtype=torch.int)
    else:
        dialog_history_ids = [int(_id) for _id in dialog_context.split(",")]  
        dialog_history_ids = torch.tensor(dialog_history_ids, dtype=torch.int32)
    
    input_ids = tokenizer.encode(f"|0|{get_length(message, tokenizer)}|" \
                                              + message + tokenizer.eos_token, return_tensors="pt")
    dialog_history_ids = torch.cat([dialog_history_ids, input_ids], dim=-1)
    input_ids = tokenizer.encode(f"|1|{next_len}|", return_tensors="pt")
    dialog_history_ids = torch.cat([dialog_history_ids, input_ids], dim=-1)
    
    return dialog_history_ids

def main():
    TOKEN = "6490789610:AAH5IQeqaOU3q1PDJX7Y_8FJaQEcWbrHktk"
    application = ApplicationBuilder().token(TOKEN).concurrent_updates(True).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("deletecontext", delete_dialog_context_in_db))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handle))
    application.run_polling()


if __name__ == '__main__':
    main()