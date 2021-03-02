import os.path
from dotenv import load_dotenv
import requests
from urllib.parse import urlparse, parse_qs, urljoin
import datetime
import logging

from google.auth.exceptions import TransportError, RefreshError
from httplib2 import ServerNotFoundError
from requests import HTTPError
from urlextract import URLExtract
import argparse
import time
from collections import namedtuple

from pydrive.drive import GoogleDrive
from pydrive.auth import GoogleAuth
from pydrive.files import ApiRequestError

import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import telegram
import vk_api
from telegram import TelegramError

WEEK_DAYS = [
    'понедельник',
    'вторник',
    'среда',
    'четверг',
    'пятница',
    'суббота',
    'воскресенье'
]

POST_FIELDS = [
    'social_vk',
    'social_tg',
    'social_fb',
    'day',
    'hour',
    'text_link',
    'image_link',
    'isPublished'
]

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

logger = logging.getLogger()


def create_parser():
    parser = argparse.ArgumentParser(description='Publish posts from Google sheet in fb, vk and tg.')
    parser.add_argument('sample_spreadsheet_id', help='The id of the Google sheet')
    parser.add_argument('sample_range_name', help='The range of data')

    return parser


def get_credentials():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds


def init_sheet_connection():
    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)

    return service.spreadsheets()


def init_google_drive_connection():
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    return GoogleDrive(gauth)


def get_sheet_data(sheet, sample_spreadsheet_id, sample_range_name):
    result = sheet.values().get(spreadsheetId=sample_spreadsheet_id,
                                range=sample_range_name, valueRenderOption='FORMULA').execute()
    return result.get('values', None)


def update_sheet_data(sheet, values, sample_spreadsheet_id, sample_range_name):
    body = {
        'values': values
    }

    sheet.values().update(
        spreadsheetId=sample_spreadsheet_id, range=sample_range_name,
        valueInputOption='USER_ENTERED', body=body).execute()


def get_content_id(id_str):
    if not id_str:
        return None

    extractor = URLExtract()
    url = extractor.find_urls(id_str)[0]
    query = urlparse(url).query
    content_id = parse_qs(query).get('id')
    if not content_id:
        return None

    return content_id[0]


def post_in_telegram(tg_token, tg_chat_id, post_img, post_text):
    bot = telegram.Bot(token=tg_token)
    if post_img:
        with open('post_images/' + post_img, 'rb') as post_img:
            bot.send_photo(chat_id=tg_chat_id, photo=post_img)
    if post_text:
        bot.send_message(chat_id=tg_chat_id, text=post_text)


def send_data_to_facebook(fb_group_id, path_url, data, files=None):
    url = urljoin('https://graph.facebook.com/', f"{fb_group_id}/{path_url}")

    if not files:
        response = requests.post(url, data=data)
        response.raise_for_status()
    else:
        response = requests.post(url, files=files, data=data)
        response.raise_for_status()

    decoded_response = response.json()
    if 'error' in decoded_response:
        raise requests.exceptions.HTTPError(decoded_response['error'])


def post_in_facebook(fb_token, fb_group_id, post_img, post_text):
    data = {
        "access_token": fb_token
    }

    if post_img:
        with open('post_images/' + post_img, 'rb') as post_img:
            files = {'upload_file': post_img}
            if post_text:
                data["caption"] = post_text
            send_data_to_facebook(fb_group_id, 'photos', data, files)
    elif post_text:
        data["message"] = post_text
        send_data_to_facebook(fb_group_id, 'feed', data)


def post_in_vkontakte(vk_login, vk_token, vk_album_id, vk_group_id, post_img, post_text):
    vk_session = vk_api.VkApi(login=vk_login, token=vk_token)
    vk_session._auth_token()

    upload = vk_api.VkUpload(vk_session)
    vk = vk_session.get_api()

    if post_img:
        photo_info = upload.photo(
            'post_images/' + post_img,
            album_id=vk_album_id,
            group_id=vk_group_id
        )
        media_id = photo_info[-1]

        if post_text:
            vk.wall.post(owner_id=f"-{vk_group_id}",
                         message=post_text,
                         attachments=f"photo-{vk_group_id}_{media_id}")
        else:
            vk.wall.post(owner_id=f"-{vk_group_id}",
                         attachments=f"photo-{vk_group_id}_{media_id}")
    elif post_text:
        vk.wall.post(owner_id=f"-{vk_group_id}",
                     message=post_text)


def get_post_image_title(drive, image_link):
    image_id = get_content_id(image_link)

    if not image_id:
        return None
    post_image = drive.CreateFile({'id': image_id})
    post_image_title = post_image['title']

    post_image.GetContentFile('post_images/' + post_image_title)

    return post_image_title


def get_post_text(drive, text_link):
    text_id = get_content_id(text_link)

    if not text_id:
        return None

    post_text_file = drive.CreateFile({'id': text_id})
    post_text_file_name = f"{post_text_file['title']}.txt"
    post_text_file.GetContentFile('post_texts/' + post_text_file_name, mimetype='text/plain')

    with open('post_texts/' + post_text_file_name, 'r', encoding="utf-8") as file:
        post_text = file.read()

    return post_text


def get_post_data(text_link, image_link):
    drive = init_google_drive_connection()
    post_image_title = get_post_image_title(drive, image_link)
    post_text = get_post_text(drive, text_link)

    return post_image_title, post_text


def publish_post(text_link, image_link, social_vk, social_tg, social_fb):
    image_title, post_text = get_post_data(text_link, image_link)

    if social_vk == 'да':
        vk_login = os.getenv("VK_LOGIN")
        vk_token = os.getenv("VK_TOKEN")
        vk_album_id = os.getenv("VK_ALBUM_ID")
        vk_group_id = os.getenv("VK_GROUP_ID")
        post_in_vkontakte(vk_login, vk_token, vk_album_id, vk_group_id, image_title, post_text)

    if social_tg == 'да':
        tg_token = os.getenv("TG_TOKEN")
        tg_chat_id = os.getenv("TG_CHAT_ID")
        post_in_telegram(tg_token, tg_chat_id, image_title, post_text)

    if social_fb == 'да':
        fb_token = os.getenv("FB_TOKEN")
        fb_group_id = os.getenv("FB_GROUP_ID")
        post_in_facebook(fb_token, fb_group_id, image_title, post_text)


def update_post_item(item, post):
    item.clear()
    for value in post:
        item.append(value)
    return item


def publish_posts(sample_spreadsheet_id, sample_range_name):
    try:
        sheet = init_sheet_connection()
        posts = get_sheet_data(sheet, sample_spreadsheet_id, sample_range_name)

        if not posts:
            return None

        Post = namedtuple('Post', POST_FIELDS)
        today = datetime.datetime.now()

        for item in posts:

            post = Post._make(item)

            now_day_index = today.weekday()

            post_day_index = WEEK_DAYS.index(post.day)
            now_hour = today.hour

            is_post_not_published = post.isPublished.lower() == 'нет'
            is_post_day_expired = now_day_index > post_day_index
            is_post_hour_expired = now_day_index == post_day_index and now_hour >= post.hour

            if is_post_not_published and (is_post_day_expired or is_post_hour_expired):
                publish_post(post.text_link, post.image_link, post.social_vk, post.social_tg, post.social_fb)
                post = post._replace(isPublished='да')
                update_post_item(item, post)

        update_sheet_data(sheet, posts, sample_spreadsheet_id, sample_range_name)
    except TelegramError as error:
        logger.exception('Can not publish post in tg: {0}'.format(error))
    except (vk_api.VkApiError, vk_api.ApiHttpError, vk_api.AuthError) as error:
        logger.exception('Can not publish post in vk: {0}'.format(error))
    except ApiRequestError as error:
        logger.exception(f'{error}')
    except HTTPError as http_err:
        logger.exception(f'HTTP error occurred: {http_err}')
    except TransportError as error:
        logger.exception(f'{error}')
    except ServerNotFoundError as error:
        logger.exception(f'{error}')
    except RefreshError as error:
        logger.exception(f'You may need to delete token.pickle {error}')
    except Exception as error:
        logger.exception(f'Other error occurred: {error}')
    finally:
        time.sleep(5)


def main():
    logging.basicConfig(
        filename='log/logging.log',
        level=logging.INFO,
        format="%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s",
    )
    logger.setLevel(logging.INFO)
    load_dotenv()
    parser = create_parser()
    args = parser.parse_args()

    while True:
        publish_posts(args.sample_spreadsheet_id, args.sample_range_name)


if __name__ == '__main__':
    main()
