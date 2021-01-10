# SMMplanner

Скрипт публикует ваш пост с описанием и фотографией в указанное время и в выбранных соц сетях: группе [ВКонтакте](https://vk.com/), группе [Facebook](https://www.facebook.com/) и канале [Telegram](https://tlgrm.ru/) из заполненной вами Google таблицей.
 [Пример таблицы](https://docs.google.com/spreadsheets/d/1Rz2tfqeF4Lc_Yh-ODrmfw8N-rmbpzPcY2p4Rjm9Vclc/edit#gid=0).

## Как запустить
 Устанавливаем необходимые библиотеки
 ```pip install requirements.txt```.
 
 Для работы скрипта необходимы ваши данные от аккаунтов социальных сетей. Чтобы их указать в папке со скриптом необходимо создать файл с именем `.env`. Открыв его с помощью любого текстового редактора, необходимо указать данные в следующем формате (без кавычек):
 ```
VK_LOGIN=your_vk_login
VK_TOKEN=your_vk_token
VK_ALBUM_ID=your_vk_album_id
VK_GROUP_ID=your_vk_group_id
TG_TOKEN=your_tg_token
TG_CHAT_ID=your_tg_chat_id
FB_TOKEN=your_fb_token
FB_GROUP_ID=your_fb_group_id
```

Как получить данные параметры: 

`VK_LOGIN` - логин от вашей страницы ВКонтакте,

`VK_TOKEN` - [инструкция](https://devman.org/qna/63/kak-poluchit-token-polzovatelja-dlja-vkontakte/), 

`VK_ALBUM_ID` - для публикации картинки в посте, необходимо предварительно создать альбом для фотографий в группе. Если зайти на страницу с альбомом, в адресной строке будет ссылка вида: https://vk.com/public{group_id}?z=album-{group_id}_{album_id},

`VK_GROUP_ID` - [инструкция](https://regvk.com/id/),

`TG_TOKEN` - [инструкция](https://smmplanner.com/blog/otlozhennyj-posting-v-telegram/), 

`TG_CHAT_ID` - ссылка на канал, например: @dvmn_flood, 

`FB_TOKEN` - [инструкция](https://developers.facebook.com/docs/graph-api/explorer/),

`FB_GROUP_ID` - id группы (взять из ссылки на неё).

Также необходимо подключить Google Sheets - [краткая инструкция](https://developers.google.com/sheets/api/quickstart/python). В результате настройки появится файл конфигурации```credentials.json```. Его необходимо поместить в корень проекта. Также необходимо авторизоваться и в PyDrive - [гайд можно найти тут](https://googleworkspace.github.io/PyDrive/docs/build/html/quickstart.html#authentication). 
 
 
 Запускаем скрипт командой 
 ```
 python script.py SAMPLE_SPREADSHEET_ID SAMPLE_RANGE_NAME 
 ```
  
 `SAMPLE_SPREADSHEET_ID` - id Google таблицы (обязательный параметр), к примеру здесь  ```https://docs.google.com/spreadsheets/d/1Rz2tfqeF4Lc_Yh-ODrmfw8N-rmbpzPcY2p4Rjm9Vclc``` id  - это ```1Rz2tfqeF4Lc_Yh-ODrmfw8N-rmbpzPcY2p4Rjm9Vclc```,

`SAMPLE_RANGE_NAME` - диапазон данных таблицы (обязательный параметр), например ```Лист1!A3:H15```.
 
 
## Цель проекта
 Код написан в образовательных целях на онлайн-курсе для веб-разработчиков [dvmn.org](https://dvmn.org/modules/) 
