import re
import logging
from pyrogram import Client, emoji, filters
from pyrogram.errors.exceptions.bad_request_400 import QueryIdInvalid
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultCachedDocument
from database.ia_filterdb import get_search_results
from yt_dlp import YoutubeDL
from utils import is_subscribed, get_size get_time, get_time_hh_mm_ss, short_num, VIDEO_DICT, get_buttons, CAPTIONS
from info import CACHE_TIME, AUTH_USERS, AUTH_CHANNEL, CUSTOM_FILE_CAPTION

logger = logging.getLogger(__name__)
cache_time = 0 if AUTH_USERS or AUTH_CHANNEL else CACHE_TIME


@Client.on_inline_query(filters.user(AUTH_USERS) if AUTH_USERS else None)
async def answer(bot, query):
    """Show search results for given inline query"""

    if AUTH_CHANNEL and not await is_subscribed(bot, query):
        await query.answer(results=[],
                           cache_time=0,
                           switch_pm_text='You have to subscribe my channel to use the bot',
                           switch_pm_parameter="subscribe")
        return

    results = []
    if '|' in query.query:
        string, file_type = query.query.split('|', maxsplit=1)
        string = string.strip()
        file_type = file_type.strip().lower()
    else:
        string = query.query.strip()
        file_type = None

    offset = int(query.offset or 0)
    reply_markup = get_reply_markup(query=string)
    files, next_offset, total = await get_search_results(string,
                                                  file_type=file_type,
                                                  max_results=10,
                                                  offset=offset)

    for file in files:
        title=file.file_name
        size=get_size(file.file_size)
        f_caption=file.caption
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption=CUSTOM_FILE_CAPTION.format(file_name=title, file_size=size, file_caption=f_caption)
            except Exception as e:
                logger.exception(e)
                f_caption=f_caption
        if f_caption is None:
            f_caption = f"{file.file_name}"
        results.append(
            InlineQueryResultCachedDocument(
                title=file.file_name,
                file_id=file.file_id,
                caption=f_caption,
                description=f'Size: {get_size(file.file_size)}\nType: {file.file_type}',
                reply_markup=reply_markup))

    if results:
        switch_pm_text = f"{emoji.FILE_FOLDER} Results - {total}"
        if string:
            switch_pm_text += f" for {string}"
        try:
            await query.answer(results=results,
                           is_personal = True,
                           cache_time=cache_time,
                           switch_pm_text=switch_pm_text,
                           switch_pm_parameter="start",
                           next_offset=str(next_offset))
        except QueryIdInvalid:
            pass
        except Exception as e:
            logging.exception(str(e))
            await query.answer(results=[], is_personal=True,
                           cache_time=cache_time,
                           switch_pm_text=str(e)[:63],
                           switch_pm_parameter="error")
    else:
        switch_pm_text = f'{emoji.CROSS_MARK} No results'
        if string:
            switch_pm_text += f' for "{string}"'

        await query.answer(results=[],
                           is_personal = True,
                           cache_time=cache_time,
                           switch_pm_text=switch_pm_text,
                           switch_pm_parameter="okay")


def get_reply_markup(query):
    buttons = [
        [
            InlineKeyboardButton('Search again', switch_inline_query_current_chat=query)
        ]
        ]
    return InlineKeyboardMarkup(buttons)

@Client.on_inline_query()
async def search(client, query):
    answers = []
    user = query.from_user.id
    string = query.query.strip().rstrip()
    keyword = string
    start, end, a_caption = None, None, None
    if '|' in string:
        times = string.split("|", 1)
    elif '?t=' in string:
        times = string.split("?t=", 1)
    elif '&t=' in string:
        times = string.split("&t=", 1)
    else:
        times = []
    if len(times) == 2:
        keyword = (times[0]).strip()
        try:
            start_, end_ = (times[1]).strip().split(None, 1)
            if "-c" in end_: # check for custom caption 
                end_, a_caption = end_.split("-c", 1)
                if a_caption:
                    CAPTIONS[query.id] = a_caption # saving captions to dict
                    a_caption = query.id
            start = get_time(start_.strip())
            end = get_time(end_.strip())
        except:
            start, end = None, None
    if string == "":
        answers.append(
            InlineQueryResultArticle(
                title="Usage Guide",
                description=("How to use me?!"),
                input_message_content=InputTextMessageContent("Just type Bot username followed by a space and your youtube query and use | or '&t=' or '?t=' to specify trim duration and make sure to separate start and end points with a space.\n\nExample: `@TrimYtbot Niram | 1:25:1 1:26:6` or `@TrimYtbot Niram | 1800 2000`\n\n__Note: You can specify timestamps either in Hour:Minute:Seconds or Minute:Seconds format or in seconds.__"),
                reply_markup=InlineKeyboardMarkup(get_buttons(start, end, get_time(0), "start", user, "", a_caption))
                )
            )
        return await query.answer(results=answers, cache_time=0)

    else:
        regex = r"^(?:https?:\/\/)?(?:www\.)?youtu\.?be(?:\.com)?\/?.*(?:watch|embed)?(?:.*v=|v\/|\/)([\w\-_]+)\&?"
        match = re.match(regex, keyword)
        if match:
            if not VIDEO_DICT.get(match.group(1)):
                try:
                    ydl_opts = {
                        "quite": True,
                        "geo-bypass": True,
                        "nocheckcertificate": True
                    }
                    with YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(keyword, download=False)                
                except:
                    return await query.answer(
                        results=answers,
                        cache_time=0,
                        switch_pm_text=("Nothing found"),
                        switch_pm_parameter="help",
                    )
                if not info:
                    return await query.answer(
                        results=answers,
                        cache_time=0,
                        switch_pm_text=("Nothing found"),
                        switch_pm_parameter="help",
                    )
                dur = get_time_hh_mm_ss(info["duration"])
                view = f'{short_num(info["view_count"])} views'
                id = info['id']
                title = info['title']
                VIDEO_DICT[id] = {'dur':dur, 'views':view, 'title':title}
            else:
                info = VIDEO_DICT.get(match.group(1))
                dur = info['dur']
                view = info['views']
                title = info['title']
                id  = match.group(1)
            buttons = get_buttons(start, end, get_time(dur), id, user, keyword, a_caption)
            caption = f"<a href=https://www.youtube.com/watch?v={id}>{title}</a>\n👀 Views: {view}\n🎞 Duration: {dur}"
            if start and end:
                caption += f"\n✂️ Selected Trim Duration: {get_time_hh_mm_ss(start)} to {get_time_hh_mm_ss(end)}"
            if len(buttons) == 1:
                caption += "\n😬 No Valid Trim Duration Specified."
            answers.append(
                InlineQueryResultPhoto(
                    photo_url=f'https://i.ytimg.com/vi/{id}/hqdefault.jpg',
                    title=title,
                    description=("Duration: {} Views: {}").format(
                        dur,
                        view
                    ),
                    caption=caption,
                    thumb_url=f'https://i.ytimg.com/vi/{id}/hqdefault.jpg',
                    reply_markup=InlineKeyboardMarkup(buttons)
                )
            )
        else:
            videosSearch = VideosSearch(keyword.lower(), limit=50)
            for v in videosSearch.result()["result"]:
                buttons = get_buttons(start, end, get_time(v["duration"]),  v['id'], user, keyword, a_caption)
                caption = f"<a href=https://www.youtube.com/watch?v={v['id']}>{v['title']}</a>\n👀 Views: {v['viewCount']['short']}\n🎞 Duration: {v['duration']}"
                if start and end:
                    caption += f"\n✂️ Selected Trim Duration: {get_time_hh_mm_ss(start)} to {get_time_hh_mm_ss(end)}"
                if len(buttons) == 1:
                    caption += "\n😬 No Valid Trim Duration Specified."
                answers.append(
                    InlineQueryResultPhoto(
                        photo_url=f'https://i.ytimg.com/vi/{v["id"]}/hqdefault.jpg',
                        title=v["title"],
                        description=("Duration: {} Views: {}").format(
                            v["duration"],
                            v["viewCount"]["short"]
                        ),
                        caption=caption,
                        thumb_url=v["thumbnails"][0]["url"],
                        reply_markup=InlineKeyboardMarkup(buttons)
                    )
                )
                VIDEO_DICT[v['id']] = {'dur':v["duration"], 'views':v["viewCount"]["short"], 'title':v['title']}
        try:
            if start and end:
                await query.answer(
                    switch_pm_text=(f"Trim from {get_time_hh_mm_ss(start)} to {get_time_hh_mm_ss(end)}"),
                    switch_pm_parameter="start",
                    results=answers,
                    cache_time=0
                )
            else:
                await query.answer(
                    results=answers,
                    cache_time=0,
                    switch_pm_text=("❌ Invalid Time Selected"),
                    switch_pm_parameter="help",
                )
        except errors.QueryIdInvalid:
            await query.answer(
                results=answers,
                cache_time=0,
                switch_pm_text=("Nothing found"),
                switch_pm_parameter="help",
            )


__handlers__ = [
    [
        InlineQueryHandler(
            search
        )
    ]
]
