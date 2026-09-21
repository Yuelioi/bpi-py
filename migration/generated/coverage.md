# 第一波迁移覆盖报告

由 `tools.migration` 生成；不要手动编辑。

源提交：`4b8d49126d34c32b0067d93d87976c3a7f97b4c5`。输入摘要：`e18b3362158fa6fabeca214c97de9bb008e54222e2382ce736bd96ff4396239b`。

## 统计

| 指标 | 数量 |
| --- | --- |
| rust_files | 307 |
| domains | 27 |
| contracts | 206 |
| response_files | 434 |
| public_async_declarations | 316 |
| type_declarations | 1159 |

## 契约关联

| 分类 | 数量 |
| --- | --- |
| flow_review | 1 |
| label_unique | 193 |
| unmatched | 9 |
| url_candidate | 3 |

## 自动化边界

请求壳模板候选：172。仍需验证参数辅助函数、类型与认证；不是可直接发布的接口。
其余声明进入人工复核，可按重复原因批量处理。

| 复核原因（可重叠） | 声明数 |
| --- | --- |
| custom_control_flow | 21 |
| custom_response_handling | 29 |
| indirect_or_multiple_requests | 13 |
| multipart | 20 |
| no_contract_match | 118 |
| session_or_mutation_contract | 6 |
| unresolved_url | 1 |
| url_match_requires_review | 5 |

## 各领域

| 领域 | 异步声明 | 契约 | 模板候选 |
| --- | --- | --- | --- |
| activity | 3 | 2 | 2 |
| article | 8 | 4 | 4 |
| audio | 20 | 16 | 16 |
| bangumi | 9 | 6 | 6 |
| cheese | 5 | 4 | 4 |
| clientinfo | 1 | 1 | 1 |
| comment | 10 | 4 | 4 |
| creativecenter | 25 | 14 | 14 |
| danmaku | 19 | 12 | 4 |
| dynamic | 20 | 13 | 13 |
| electric | 13 | 10 | 5 |
| fav | 13 | 6 | 6 |
| historytoview | 9 | 3 | 3 |
| live | 34 | 20 | 15 |
| login | 16 | 13 | 9 |
| manga | 13 | 5 | 5 |
| message | 4 | 3 | 3 |
| misc | 5 | 4 | 1 |
| note | 9 | 7 | 7 |
| opus | 1 | 1 | 1 |
| search | 11 | 11 | 2 |
| user | 25 | 16 | 16 |
| video | 27 | 17 | 17 |
| video_ranking | 9 | 9 | 9 |
| vip | 3 | 1 | 1 |
| wallet | 1 | 1 | 1 |
| web_widget | 3 | 3 | 3 |

## 契约 → 源码

| 契约 | 风险 | 关联状态 | 源码声明 |
| --- | --- | --- | --- |
| activity.info | public-read | label_unique | src/activity/client.rs:30:ActivityClient<'a>::info |
| activity.list | public-read | label_unique | src/activity/client.rs:39:ActivityClient<'a>::list |
| article.articles_info | public-read | label_unique | src/article/client.rs:78:ArticleClient<'a>::articles |
| article.cards | authenticated-read | label_unique | src/article/client.rs:67:ArticleClient<'a>::cards |
| article.info | public-read | label_unique | src/article/client.rs:47:ArticleClient<'a>::info |
| article.view | authenticated-read | label_unique | src/article/client.rs:56:ArticleClient<'a>::view |
| audio.coin_count | authenticated-read | label_unique | src/audio/client.rs:183:AudioClient<'a>::coin_count |
| audio.collection_info | authenticated-read | label_unique | src/audio/client.rs:226:AudioClient<'a>::collection_info |
| audio.collection_status | authenticated-read | label_unique | src/audio/client.rs:174:AudioClient<'a>::collection_status |
| audio.collections_list | authenticated-read | label_unique | src/audio/client.rs:214:AudioClient<'a>::collections_list |
| audio.hot_menu | public-read | label_unique | src/audio/client.rs:238:AudioClient<'a>::hot_menu |
| audio.info | public-read | label_unique | src/audio/client.rs:129:AudioClient<'a>::info |
| audio.lyric | public-read | label_unique | src/audio/client.rs:156:AudioClient<'a>::lyric |
| audio.members | public-read | label_unique | src/audio/client.rs:147:AudioClient<'a>::members |
| audio.rank_detail | public-read | label_unique | src/audio/client.rs:270:AudioClient<'a>::rank_detail |
| audio.rank_menu | public-read | label_unique | src/audio/client.rs:247:AudioClient<'a>::rank_menu |
| audio.rank_music_list | public-read | label_unique | src/audio/client.rs:281:AudioClient<'a>::rank_music_list |
| audio.rank_period | public-read | label_unique | src/audio/client.rs:256:AudioClient<'a>::rank_period |
| audio.status_number | public-read | label_unique | src/audio/client.rs:165:AudioClient<'a>::status_number |
| audio.stream_url | public-read | label_unique | src/audio/client.rs:204:AudioClient<'a>::stream_url |
| audio.stream_url_web | public-read | label_unique | src/audio/client.rs:192:AudioClient<'a>::stream_url_web |
| audio.tags | public-read | label_unique | src/audio/client.rs:138:AudioClient<'a>::tags |
| bangumi.info.review_user | public-read | label_unique | src/bangumi/client.rs:54:BangumiClient<'a>::info |
| bangumi.info.season_detail_by_ep_id | public-read | label_unique | src/bangumi/client.rs:63:BangumiClient<'a>::detail; src/bangumi/client.rs:72:BangumiClient<'a>::detail_by_season_id; src/bangumi/client.rs:81:BangumiClient<'a>::detail_by_ep_id |
| bangumi.info.season_detail_by_season_id | public-read | label_unique | src/bangumi/client.rs:63:BangumiClient<'a>::detail; src/bangumi/client.rs:72:BangumiClient<'a>::detail_by_season_id; src/bangumi/client.rs:81:BangumiClient<'a>::detail_by_ep_id |
| bangumi.info.season_section | public-read | label_unique | src/bangumi/client.rs:90:BangumiClient<'a>::sections |
| bangumi.playurl | public-read | label_unique | src/bangumi/client.rs:111:BangumiClient<'a>::video_stream |
| bangumi.timeline | public-read | label_unique | src/bangumi/client.rs:99:BangumiClient<'a>::timeline |
| cheese.info.ep_list | public-read | label_unique | src/cheese/client.rs:65:CheeseClient<'a>::ep_list |
| cheese.info.season_detail_by_ep_id | public-read | label_unique | src/cheese/client.rs:38:CheeseClient<'a>::info; src/cheese/client.rs:47:CheeseClient<'a>::info_by_season_id; src/cheese/client.rs:56:CheeseClient<'a>::info_by_ep_id |
| cheese.info.season_detail_by_season_id | public-read | label_unique | src/cheese/client.rs:38:CheeseClient<'a>::info; src/cheese/client.rs:47:CheeseClient<'a>::info_by_season_id; src/cheese/client.rs:56:CheeseClient<'a>::info_by_ep_id |
| cheese.playurl | public-read | label_unique | src/cheese/client.rs:74:CheeseClient<'a>::video_stream |
| clientinfo.ip | public-read | label_unique | src/clientinfo/client.rs:25:ClientInfoClient<'a>::ip |
| comment.read.count | public-read | label_unique | src/comment/client.rs:71:CommentClient<'a>::count |
| comment.read.hot | public-read | label_unique | src/comment/client.rs:62:CommentClient<'a>::hot |
| comment.read.list | public-read | label_unique | src/comment/client.rs:44:CommentClient<'a>::list |
| comment.read.replies | public-read | label_unique | src/comment/client.rs:53:CommentClient<'a>::replies |
| creativecenter.railgun.electromagnetic_info | private-read | label_unique | src/creativecenter/client.rs:245:CreativeCenterClient<'a>::electromagnetic_info |
| creativecenter.season.aid | private-read | label_unique | src/creativecenter/client.rs:137:CreativeCenterClient<'a>::season_by_aid |
| creativecenter.season.info | private-read | label_unique | src/creativecenter/client.rs:128:CreativeCenterClient<'a>::season_info |
| creativecenter.season.list | private-read | label_unique | src/creativecenter/client.rs:119:CreativeCenterClient<'a>::season_list |
| creativecenter.season.section | private-read | label_unique | src/creativecenter/client.rs:146:CreativeCenterClient<'a>::season_section_episodes |
| creativecenter.statistics.archive_compare | private-read | label_unique | src/creativecenter/client.rs:187:CreativeCenterClient<'a>::archive_compare |
| creativecenter.statistics.article_stat | private-read | label_unique | src/creativecenter/client.rs:199:CreativeCenterClient<'a>::article_stat |
| creativecenter.statistics.article_trend | private-read | label_unique | src/creativecenter/client.rs:216:CreativeCenterClient<'a>::article_trend |
| creativecenter.statistics.play_source | private-read | label_unique | src/creativecenter/client.rs:228:CreativeCenterClient<'a>::play_source |
| creativecenter.statistics.up_stat | private-read | label_unique | src/creativecenter/client.rs:179:CreativeCenterClient<'a>::up_stat |
| creativecenter.statistics.video_trend | private-read | label_unique | src/creativecenter/client.rs:207:CreativeCenterClient<'a>::video_trend |
| creativecenter.statistics.viewer_data | private-read | label_unique | src/creativecenter/client.rs:237:CreativeCenterClient<'a>::viewer_data |
| creativecenter.videos.archive_videos | private-read | label_unique | src/creativecenter/client.rs:167:CreativeCenterClient<'a>::archive_videos |
| creativecenter.videos.archives_list | private-read | label_unique | src/creativecenter/client.rs:158:CreativeCenterClient<'a>::archives_list |
| danmaku.history.xml | authenticated-read | label_unique | src/danmaku/client.rs:187:DanmakuClient<'a>::history_xml_bytes |
| danmaku.adv.state | authenticated-read | label_unique | src/danmaku/client.rs:123:DanmakuClient<'a>::adv_state |
| danmaku.history.dates | authenticated-read | label_unique | src/danmaku/client.rs:90:DanmakuClient<'a>::history_dates |
| danmaku.snapshot | public-read | label_unique | src/danmaku/client.rs:102:DanmakuClient<'a>::snapshot |
| danmaku.thumbup.stats | public-read | label_unique | src/danmaku/client.rs:111:DanmakuClient<'a>::thumbup_stats |
| danmaku.mobile.seg | public-read | label_unique | src/danmaku/client.rs:164:DanmakuClient<'a>::mobile_seg_proto |
| danmaku.web.history_seg | authenticated-read | label_unique | src/danmaku/client.rs:174:DanmakuClient<'a>::web_history_seg_proto |
| danmaku.web.seg | public-read | label_unique | src/danmaku/client.rs:132:DanmakuClient<'a>::web_seg_proto |
| danmaku.web.seg_wbi | public-read | label_unique | src/danmaku/client.rs:142:DanmakuClient<'a>::web_seg_wbi_proto |
| danmaku.web.view | public-read | label_unique | src/danmaku/client.rs:154:DanmakuClient<'a>::web_view_proto |
| danmaku.xml.comment_xml | public-read | unmatched | — |
| danmaku.xml.list_so | public-read | url_candidate | src/danmaku/client.rs:196:DanmakuClient<'a>::xml_list_so |
| dynamic.live_users | authenticated-read | label_unique | src/dynamic/client.rs:219:DynamicClient<'a>::live_users |
| dynamic.recent_up | authenticated-read | label_unique | src/dynamic/client.rs:237:DynamicClient<'a>::recent_up |
| dynamic.up_users | authenticated-read | label_unique | src/dynamic/client.rs:228:DynamicClient<'a>::up_users |
| dynamic.detail | public-read | label_unique | src/dynamic/client.rs:154:DynamicClient<'a>::detail |
| dynamic.detail_forward_item | authenticated-read | label_unique | src/dynamic/client.rs:207:DynamicClient<'a>::forward_item |
| dynamic.detail_forward | public-read | label_unique | src/dynamic/client.rs:189:DynamicClient<'a>::forwards |
| dynamic.detail_pic | public-read | label_unique | src/dynamic/client.rs:198:DynamicClient<'a>::pics |
| dynamic.detail_reaction | public-read | label_unique | src/dynamic/client.rs:163:DynamicClient<'a>::reactions |
| dynamic.feed_all | authenticated-read | label_unique | src/dynamic/client.rs:114:DynamicClient<'a>::all |
| dynamic.feed_banner | public-read | label_unique | src/dynamic/client.rs:141:DynamicClient<'a>::feed_banner |
| dynamic.feed_all_update | authenticated-read | label_unique | src/dynamic/client.rs:123:DynamicClient<'a>::check_new |
| dynamic.feed_nav | authenticated-read | label_unique | src/dynamic/client.rs:132:DynamicClient<'a>::nav_feed |
| dynamic.lottery_notice | public-read | label_unique | src/dynamic/client.rs:175:DynamicClient<'a>::lottery_notice |
| electric.charge_follow_info | private-read | label_unique | src/electric/client.rs:172:ElectricClient<'a>::charge_follow_info |
| electric.charge_record | private-read | label_unique | src/electric/client.rs:153:ElectricClient<'a>::charge_record |
| electric.rank_recent | private-read | label_unique | src/electric/client.rs:139:ElectricClient<'a>::rank_recent |
| electric.recharge_list | private-read | label_unique | src/electric/client.rs:115:ElectricClient<'a>::recharge_list |
| electric.remark_detail | private-read | label_unique | src/electric/client.rs:230:ElectricClient<'a>::remark_detail |
| electric.remark_list | private-read | label_unique | src/electric/client.rs:204:ElectricClient<'a>::remark_list |
| electric.month_up_list | public-read | label_unique | src/electric/client.rs:87:ElectricClient<'a>::month_up_list |
| electric.upower_item_detail | public-read | label_unique | src/electric/client.rs:163:ElectricClient<'a>::upower_item_detail |
| electric.upower_member_rank | public-read | label_unique | src/electric/client.rs:181:ElectricClient<'a>::upower_member_rank |
| electric.video_show | public-read | label_unique | src/electric/client.rs:96:ElectricClient<'a>::video_show |
| fav.collected_list | private-read | label_unique | src/fav/client.rs:81:FavClient<'a>::collected_list |
| fav.created_list | private-read | label_unique | src/fav/client.rs:69:FavClient<'a>::created_list |
| fav.folder_info | private-read | label_unique | src/fav/client.rs:60:FavClient<'a>::folder_info |
| fav.list_detail | private-read | label_unique | src/fav/client.rs:105:FavClient<'a>::list_detail |
| fav.resource_ids | private-read | label_unique | src/fav/client.rs:114:FavClient<'a>::resource_ids |
| fav.resource_infos | private-read | label_unique | src/fav/client.rs:93:FavClient<'a>::resource_infos |
| historytoview.history_list | private-read | label_unique | src/historytoview/client.rs:37:HistoryToViewClient<'a>::history_list |
| historytoview.history_shadow | private-read | label_unique | src/historytoview/client.rs:46:HistoryToViewClient<'a>::history_shadow |
| historytoview.toview_list | private-read | label_unique | src/historytoview/client.rs:54:HistoryToViewClient<'a>::toview_list |
| live.follow_up_list | private-read | label_unique | src/live/client.rs:269:LiveClient<'a>::follow_up_list |
| live.follow_up_web_list | private-read | label_unique | src/live/client.rs:300:LiveClient<'a>::follow_up_web_list |
| live.my_medals | private-read | label_unique | src/live/client.rs:256:LiveClient<'a>::my_medals |
| live.replay_list | private-read | label_unique | src/live/client.rs:316:LiveClient<'a>::replay_list |
| live.blind_gift_info | authenticated-read | label_unique | src/live/client.rs:200:LiveClient<'a>::blind_gift_info |
| live.gift_types | authenticated-read | label_unique | src/live/client.rs:163:LiveClient<'a>::gift_types |
| live.room_gift_list | public-read | label_unique | src/live/client.rs:172:LiveClient<'a>::room_gift_list |
| live.guard_list | public-read | label_unique | src/live/client.rs:339:LiveClient<'a>::guard_list |
| live.banned_users | private-read | label_unique | src/live/client.rs:380:LiveClient<'a>::banned_users |
| live.shield_keywords | private-read | label_unique | src/live/client.rs:396:LiveClient<'a>::shield_keywords |
| live.silent_users | private-read | label_unique | src/live/client.rs:364:LiveClient<'a>::silent_users |
| live.area_list | public-read | label_unique | src/live/client.rs:96:LiveClient<'a>::area_list |
| live.recommend | public-read | label_unique | src/live/client.rs:143:LiveClient<'a>::recommend |
| live.room_info | public-read | label_unique | src/live/client.rs:105:LiveClient<'a>::room_info |
| live.stream | public-read | label_unique | src/live/client.rs:115:LiveClient<'a>::stream |
| live.version | public-read | label_unique | src/live/client.rs:153:LiveClient<'a>::version |
| live.danmu_info | authenticated-read | label_unique | src/live/client.rs:210:LiveClient<'a>::danmu_info |
| live.emoticons | authenticated-read | label_unique | src/live/client.rs:228:LiveClient<'a>::emoticons |
| live.lottery_info | authenticated-read | label_unique | src/live/client.rs:241:LiveClient<'a>::lottery_info |
| live.web_heart_beat | public-read | label_unique | src/live/client.rs:412:LiveClient<'a>::web_heart_beat |
| login.account_info | private-read | label_unique | src/login/client.rs:139:LoginClient<'a>::account_info |
| login.captcha_generate | login-session | label_unique | src/login/client.rs:175:LoginClient<'a>::generate_captcha |
| login.coin | private-read | label_unique | src/login/client.rs:115:LoginClient<'a>::coin |
| login.daily_reward | authenticated-read | label_unique | src/login/client.rs:131:LoginClient<'a>::daily_reward |
| login.nav | private-read | label_unique | src/login/client.rs:99:LoginClient<'a>::nav |
| login.log | private-read | label_unique | src/login/client.rs:165:LoginClient<'a>::log |
| login.notice | private-read | label_unique | src/login/client.rs:155:LoginClient<'a>::notice |
| login.qr.flow | login-session | flow_review | src/login/client.rs:193:LoginClient<'a>::qr_generate; src/login/client.rs:202:LoginClient<'a>::qr_poll |
| login.qr_generate | login-session | label_unique | src/login/client.rs:193:LoginClient<'a>::qr_generate |
| login.qr_poll | login-session | url_candidate | src/login/client.rs:202:LoginClient<'a>::qr_poll |
| login.stat | private-read | label_unique | src/login/client.rs:107:LoginClient<'a>::stat |
| login.today_coin_exp | private-read | label_unique | src/login/client.rs:123:LoginClient<'a>::today_coin_exp |
| login.vip_info | authenticated-read | label_unique | src/login/client.rs:147:LoginClient<'a>::vip_info |
| manga.clock_in_info | public-read | label_unique | src/manga/client.rs:61:MangaClient<'a>::clock_in_info |
| manga.coupons | public-read | label_unique | src/manga/client.rs:85:MangaClient<'a>::coupons |
| manga.point_products | public-read | label_unique | src/manga/client.rs:77:MangaClient<'a>::point_products |
| manga.season_info | public-read | label_unique | src/manga/client.rs:53:MangaClient<'a>::season_info |
| manga.user_point | public-read | label_unique | src/manga/client.rs:69:MangaClient<'a>::user_point |
| message.reply_feed | private-read | label_unique | src/message/client.rs:52:MessageClient<'a>::reply_feed |
| message.single_unread | private-read | label_unique | src/message/client.rs:61:MessageClient<'a>::single_unread |
| message.unread_count | private-read | label_unique | src/message/client.rs:40:MessageClient<'a>::unread_count |
| misc.b23tv.short_link | public-read | label_unique | src/misc/client.rs:64:MiscClient<'a>::b23_short_link |
| misc.buvid | login-session | label_unique | src/misc/client.rs:56:MiscClient<'a>::buvid |
| misc.buvid3 | login-session | label_unique | src/misc/client.rs:48:MiscClient<'a>::buvid3 |
| misc.bili_ticket | login-session | label_unique | src/misc/client.rs:76:MiscClient<'a>::bili_ticket |
| note.archive_list | authenticated-read | label_unique | src/note/client.rs:96:NoteClient<'a>::archive_list |
| note.is_forbid | public-read | label_unique | src/note/client.rs:66:NoteClient<'a>::is_forbid |
| note.private_info | private-read | label_unique | src/note/client.rs:75:NoteClient<'a>::private_info |
| note.public_archive_list | public-read | label_unique | src/note/client.rs:120:NoteClient<'a>::public_archive_list |
| note.public_info | public-read | label_unique | src/note/client.rs:87:NoteClient<'a>::public_info |
| note.user_private_list | private-read | label_unique | src/note/client.rs:108:NoteClient<'a>::user_private_list |
| note.user_public_list | public-read | label_unique | src/note/client.rs:132:NoteClient<'a>::user_public_list |
| opus.space_feed | public-read | label_unique | src/opus/client.rs:24:OpusClient<'a>::space_feed |
| search.article | public-read | unmatched | — |
| search.bangumi | public-read | unmatched | — |
| search.bili_user | public-read | unmatched | — |
| search.default | public-read | label_unique | src/search/client.rs:111:SearchClient<'a>::default |
| search.hotwords | public-read | url_candidate | src/search/client.rs:131:SearchClient<'a>::hotwords |
| search.live | public-read | unmatched | — |
| search.live_room | public-read | unmatched | — |
| search.live_user | public-read | unmatched | — |
| search.movie | public-read | unmatched | — |
| search.suggest | public-read | label_unique | src/search/client.rs:122:SearchClient<'a>::suggest |
| search.video | public-read | unmatched | — |
| user.album_count | public-read | label_unique | src/user/client.rs:151:UserClient<'a>::album_count |
| user.bangumi_follow_list | public-read | label_unique | src/user/client.rs:160:UserClient<'a>::bangumi_follow_list |
| user.card | public-read | label_unique | src/user/client.rs:124:UserClient<'a>::card |
| user.cards | authenticated-read | label_unique | src/user/client.rs:133:UserClient<'a>::cards |
| user.infos | authenticated-read | label_unique | src/user/client.rs:142:UserClient<'a>::infos |
| user.medal_wall | authenticated-read | label_unique | src/user/client.rs:202:UserClient<'a>::medal_wall |
| user.name_to_uid | authenticated-read | label_unique | src/user/client.rs:212:UserClient<'a>::name_to_uid |
| user.nav_stat | public-read | label_unique | src/user/client.rs:233:UserClient<'a>::nav_stat |
| user.relation_stat | public-read | label_unique | src/user/client.rs:221:UserClient<'a>::relation_stat |
| user.space_info | authenticated-read | label_unique | src/user/client.rs:251:UserClient<'a>::space_info |
| user.space_notice | public-read | label_unique | src/user/client.rs:262:UserClient<'a>::space_notice |
| user.up_stat | public-read | label_unique | src/user/client.rs:242:UserClient<'a>::up_stat |
| user.uploaded_videos | public-read | label_unique | src/user/client.rs:271:UserClient<'a>::uploaded_videos |
| user.follow_tags | private-read | label_unique | src/user/client.rs:193:UserClient<'a>::follow_tags |
| user.followers | private-read | label_unique | src/user/client.rs:183:UserClient<'a>::followers |
| user.followings | private-read | label_unique | src/user/client.rs:173:UserClient<'a>::followings |
| video.collection.home_seasons_series | public-read | label_unique | src/video/client.rs:128:VideoClient<'a>::home_seasons_series |
| video.collection.seasons_archives_list | public-read | label_unique | src/video/client.rs:113:VideoClient<'a>::seasons_archives_list |
| video.collection.seasons_series_list | public-read | label_unique | src/video/client.rs:142:VideoClient<'a>::seasons_series_list |
| video.collection.series_archives | public-read | label_unique | src/video/client.rs:168:VideoClient<'a>::series_archives |
| video.collection.series_info | public-read | label_unique | src/video/client.rs:156:VideoClient<'a>::series_info |
| video.desc | public-read | label_unique | src/video/client.rs:92:VideoClient<'a>::desc |
| video.detail | public-read | label_unique | src/video/client.rs:74:VideoClient<'a>::detail |
| video.pagelist | public-read | label_unique | src/video/client.rs:83:VideoClient<'a>::page_list |
| video.view | public-read | label_unique | src/video/client.rs:65:VideoClient<'a>::view |
| video.ai_summary | authenticated-read | label_unique | src/video/client.rs:229:VideoClient<'a>::ai_summary |
| video.homepage_recommendations | public-read | label_unique | src/video/client.rs:215:VideoClient<'a>::homepage_recommendations |
| video.interactive_video_info | public-read | label_unique | src/video/client.rs:252:VideoClient<'a>::interactive_video_info |
| video.online_total | public-read | label_unique | src/video/client.rs:180:VideoClient<'a>::online_total |
| video.player_info_v2 | public-read | label_unique | src/video/client.rs:192:VideoClient<'a>::player_info_v2 |
| video.related_videos | public-read | label_unique | src/video/client.rs:206:VideoClient<'a>::related_videos |
| video.tags | public-read | label_unique | src/video/client.rs:243:VideoClient<'a>::tags |
| video.play_url | public-read | label_unique | src/video/client.rs:101:VideoClient<'a>::play_url |
| video_ranking.popular_list | public-read | label_unique | src/video_ranking/client.rs:74:VideoRankingClient<'a>::popular_list |
| video_ranking.popular_precious | public-read | label_unique | src/video_ranking/client.rs:105:VideoRankingClient<'a>::popular_precious |
| video_ranking.popular_series_list | public-read | label_unique | src/video_ranking/client.rs:83:VideoRankingClient<'a>::popular_series_list |
| video_ranking.popular_series_one | public-read | label_unique | src/video_ranking/client.rs:91:VideoRankingClient<'a>::popular_series_one |
| video_ranking.ranking_list | public-read | label_unique | src/video_ranking/client.rs:113:VideoRankingClient<'a>::ranking_list |
| video_ranking.region_dynamic | authenticated-read | label_unique | src/video_ranking/client.rs:122:VideoRankingClient<'a>::region_dynamic |
| video_ranking.region_newlist | public-read | label_unique | src/video_ranking/client.rs:146:VideoRankingClient<'a>::region_newlist |
| video_ranking.region_newlist_rank | public-read | label_unique | src/video_ranking/client.rs:158:VideoRankingClient<'a>::region_newlist_rank |
| video_ranking.region_tag_dynamic | public-read | label_unique | src/video_ranking/client.rs:134:VideoRankingClient<'a>::region_tag_dynamic |
| vip.center_info | public-read | label_unique | src/vip/client.rs:24:VipClient<'a>::center_info |
| wallet.info | private-read | label_unique | src/wallet/client.rs:23:WalletClient<'a>::info |
| web_widget.header_page | public-read | label_unique | src/web_widget/client.rs:50:WebWidgetClient<'a>::header_page |
| web_widget.online | public-read | label_unique | src/web_widget/client.rs:62:WebWidgetClient<'a>::online |
| web_widget.region_banner | public-read | label_unique | src/web_widget/client.rs:38:WebWidgetClient<'a>::region_banner |

## 无契约匹配的公开异步声明

包含旧方法和辅助方法；不把这些数量直接等同于缺失端点数。

| 声明 | 请求 / 返回处理 |
| --- | --- |
| src/activity/client.rs:48:ActivityClient<'a>::list_default | no_contract_match, indirect_or_multiple_requests, custom_response_handling |
| src/article/action.rs:25:ArticleClient<'a>::like | no_contract_match |
| src/article/action.rs:36:ArticleClient<'a>::coin | no_contract_match |
| src/article/action.rs:47:ArticleClient<'a>::favorite | no_contract_match |
| src/article/action.rs:61:ArticleClient<'a>::unfavorite | no_contract_match |
| src/audio/action.rs:26:AudioClient<'a>::favorite | no_contract_match |
| src/audio/action.rs:37:AudioClient<'a>::collect | no_contract_match |
| src/audio/action.rs:48:AudioClient<'a>::coin | no_contract_match |
| src/audio/rank.rs:118:AudioClient<'a>::subscribe_rank | no_contract_match |
| src/bangumi/follow.rs:43:BangumiClient<'a>::follow | no_contract_match |
| src/bangumi/follow.rs:54:BangumiClient<'a>::unfollow | no_contract_match |
| src/comment/action.rs:229:CommentClient<'a>::add | no_contract_match |
| src/comment/action.rs:239:CommentClient<'a>::like | no_contract_match |
| src/comment/action.rs:249:CommentClient<'a>::dislike | no_contract_match |
| src/comment/action.rs:262:CommentClient<'a>::delete | no_contract_match |
| src/comment/action.rs:275:CommentClient<'a>::top | no_contract_match |
| src/comment/action.rs:285:CommentClient<'a>::report | no_contract_match |
| src/creativecenter/opus.rs:20:CreativeCenterClient<'a>::dynamic_delete | no_contract_match |
| src/creativecenter/opus.rs:42:CreativeCenterClient<'a>::article_delete | no_contract_match |
| src/creativecenter/season/action.rs:42:CreativeCenterClient<'a>::season_create | no_contract_match, custom_control_flow |
| src/creativecenter/season/action.rs:83:CreativeCenterClient<'a>::season_delete | no_contract_match |
| src/creativecenter/season/action.rs:107:CreativeCenterClient<'a>::season_episodes_add | no_contract_match |
| src/creativecenter/season/edit.rs:108:CreativeCenterClient<'a>::season_edit | no_contract_match |
| src/creativecenter/season/edit.rs:139:CreativeCenterClient<'a>::season_section_edit | no_contract_match |
| src/creativecenter/season/edit.rs:171:CreativeCenterClient<'a>::season_section_episode_edit | no_contract_match |
| src/creativecenter/season/edit.rs:192:CreativeCenterClient<'a>::season_enable_section | no_contract_match |
| src/creativecenter/season/edit.rs:224:CreativeCenterClient<'a>::season_section_add_episodes | no_contract_match |
| src/creativecenter/upload.rs:37:CreativeCenterClient<'a>::upload_cover | no_contract_match, custom_control_flow |
| src/danmaku/action.rs:364:DanmakuClient<'a>::send | no_contract_match |
| src/danmaku/action.rs:380:DanmakuClient<'a>::recall | no_contract_match |
| src/danmaku/action.rs:393:DanmakuClient<'a>::buy_adv | no_contract_match |
| src/danmaku/action.rs:406:DanmakuClient<'a>::thumbup | no_contract_match |
| src/danmaku/action.rs:420:DanmakuClient<'a>::report | no_contract_match |
| src/danmaku/action.rs:434:DanmakuClient<'a>::edit_state | no_contract_match |
| src/danmaku/action.rs:448:DanmakuClient<'a>::edit_pool | no_contract_match |
| src/danmaku/client.rs:209:DanmakuClient<'a>::xml_list | no_contract_match, unresolved_url, custom_response_handling |
| src/dynamic/action.rs:83:DynamicClient<'a>::like | no_contract_match |
| src/dynamic/action.rs:96:DynamicClient<'a>::delete_draft | no_contract_match |
| src/dynamic/action.rs:110:DynamicClient<'a>::set_top | no_contract_match |
| src/dynamic/action.rs:123:DynamicClient<'a>::remove_top | no_contract_match |
| src/dynamic/publish.rs:243:DynamicClient<'a>::upload_pic | no_contract_match, custom_control_flow, multipart |
| src/dynamic/publish.rs:274:DynamicClient<'a>::create_text | no_contract_match, multipart |
| src/dynamic/publish.rs:295:DynamicClient<'a>::create_complex | no_contract_match |
| src/electric/bcoin.rs:93:ElectricClient<'a>::bcoin_quick_pay | no_contract_match |
| src/electric/charge_msg.rs:138:ElectricClient<'a>::send_message | no_contract_match |
| src/electric/charge_msg.rs:152:ElectricClient<'a>::reply_remark | no_contract_match |
| src/fav/action.rs:20:FavClient<'a>::add_folder | no_contract_match |
| src/fav/action.rs:30:FavClient<'a>::edit_folder | no_contract_match |
| src/fav/action.rs:40:FavClient<'a>::delete_folders | no_contract_match |
| src/fav/action.rs:50:FavClient<'a>::copy_resources | no_contract_match |
| src/fav/action.rs:60:FavClient<'a>::move_resources | no_contract_match |
| src/fav/action.rs:70:FavClient<'a>::delete_resources | no_contract_match |
| src/fav/action.rs:80:FavClient<'a>::clean_resources | no_contract_match |
| src/historytoview/history.rs:130:HistoryToViewClient<'a>::delete_history | no_contract_match |
| src/historytoview/history.rs:144:HistoryToViewClient<'a>::clear_history | no_contract_match |
| src/historytoview/history.rs:157:HistoryToViewClient<'a>::set_history_shadow | no_contract_match |
| src/historytoview/toview.rs:148:HistoryToViewClient<'a>::add_toview | no_contract_match |
| src/historytoview/toview.rs:162:HistoryToViewClient<'a>::delete_toview | no_contract_match |
| src/historytoview/toview.rs:176:HistoryToViewClient<'a>::clear_toview | no_contract_match |
| src/live/danmaku.rs:47:LiveClient<'a>::live_send_danmu | no_contract_match, custom_control_flow, multipart |
| src/live/manage.rs:103:LiveClient<'a>::live_create_room | no_contract_match, multipart |
| src/live/manage.rs:126:LiveClient<'a>::live_update_room_info | no_contract_match, custom_control_flow, multipart |
| src/live/manage.rs:161:LiveClient<'a>::live_fetch_web_up_stream_addr | no_contract_match |
| src/live/manage.rs:173:LiveClient<'a>::live_web_center_start | no_contract_match |
| src/live/manage.rs:218:LiveClient<'a>::live_stop | no_contract_match, multipart |
| src/live/manage.rs:238:LiveClient<'a>::live_update_pre_live_info | no_contract_match, custom_control_flow, multipart |
| src/live/manage.rs:271:LiveClient<'a>::live_update_room_news | no_contract_match, multipart |
| src/live/silent_user_manage.rs:237:LiveClient<'a>::live_add_silent_user | no_contract_match |
| src/live/silent_user_manage.rs:277:LiveClient<'a>::live_del_block_user | no_contract_match |
| src/live/silent_user_manage.rs:300:LiveClient<'a>::live_add_banned_user | no_contract_match |
| src/live/silent_user_manage.rs:327:LiveClient<'a>::live_del_banned_user | no_contract_match |
| src/live/silent_user_manage.rs:356:LiveClient<'a>::live_add_shield_keyword | no_contract_match |
| src/live/silent_user_manage.rs:383:LiveClient<'a>::live_del_shield_keyword | no_contract_match |
| src/login/exit.rs:72:LoginClient<'a>::logout | no_contract_match |
| src/login/login_action/sms.rs:100:LoginClient<'a>::send_sms_code | no_contract_match |
| src/login/login_action/sms.rs:114:LoginClient<'a>::login_with_sms | no_contract_match, custom_control_flow, custom_response_handling |
| src/login/member_center/sign.rs:41:LoginClient<'a>::update_user_sign | no_contract_match |
| src/manga/activity.rs:28:MangaClient<'a>::manga_share_comic | no_contract_match, custom_response_handling |
| src/manga/clockin.rs:72:MangaClient<'a>::manga_clock_in | no_contract_match, custom_response_handling |
| src/manga/clockin.rs:92:MangaClient<'a>::manga_clock_in_makeup | no_contract_match, custom_response_handling |
| src/manga/comic.rs:55:MangaClient<'a>::manga_buy_episode | no_contract_match, custom_response_handling |
| src/manga/comic.rs:72:MangaClient<'a>::manga_buy_episode_with_coupon | no_contract_match, indirect_or_multiple_requests, custom_response_handling |
| src/manga/comic.rs:93:MangaClient<'a>::manga_buy_episode_with_free | no_contract_match, indirect_or_multiple_requests, custom_response_handling |
| src/manga/comic.rs:114:MangaClient<'a>::manga_buy_episode_with_general_coupon | no_contract_match, indirect_or_multiple_requests, custom_response_handling |
| src/manga/point_shop.rs:107:MangaClient<'a>::manga_point_exchange | no_contract_match, custom_response_handling |
| src/message/private_msg.rs:105:MessageClient<'a>::send | no_contract_match, custom_control_flow |
| src/misc/client.rs:92:MiscClient<'a>::bili_ticket_string | no_contract_match, indirect_or_multiple_requests, custom_control_flow, custom_response_handling |
| src/note/action.rs:173:NoteClient<'a>::add | no_contract_match |
| src/note/action.rs:185:NoteClient<'a>::delete | no_contract_match |
| src/search/client.rs:49:SearchClient<'a>::article | no_contract_match, indirect_or_multiple_requests, custom_response_handling |
| src/search/client.rs:58:SearchClient<'a>::bangumi | no_contract_match, indirect_or_multiple_requests, custom_response_handling |
| src/search/client.rs:67:SearchClient<'a>::bili_user | no_contract_match, indirect_or_multiple_requests, custom_response_handling |
| src/search/client.rs:76:SearchClient<'a>::live | no_contract_match, indirect_or_multiple_requests, custom_response_handling |
| src/search/client.rs:81:SearchClient<'a>::live_room | no_contract_match, indirect_or_multiple_requests, custom_response_handling |
| src/search/client.rs:90:SearchClient<'a>::live_user | no_contract_match, indirect_or_multiple_requests, custom_response_handling |
| src/search/client.rs:99:SearchClient<'a>::movie | no_contract_match, indirect_or_multiple_requests, custom_response_handling |
| src/search/client.rs:105:SearchClient<'a>::video | no_contract_match, indirect_or_multiple_requests, custom_response_handling |
| src/user/relation/action.rs:132:UserClient<'a>::modify_relation | no_contract_match, multipart |
| src/user/relation/group.rs:140:UserClient<'a>::create_group_tag | no_contract_match, multipart |
| src/user/relation/group.rs:154:UserClient<'a>::update_group_tag | no_contract_match, multipart |
| src/user/relation/group.rs:168:UserClient<'a>::delete_group_tag | no_contract_match, multipart |
| src/user/relation/group.rs:182:UserClient<'a>::add_group_users_to_tags | no_contract_match, multipart |
| src/user/relation/group.rs:196:UserClient<'a>::remove_group_users | no_contract_match, multipart |
| src/user/relation/group.rs:210:UserClient<'a>::copy_group_users_to_tags | no_contract_match, multipart |
| src/user/relation/group.rs:224:UserClient<'a>::move_group_users_to_tags | no_contract_match, multipart |
| src/user/space.rs:252:UserClient<'a>::set_space_notice | no_contract_match, multipart |
| src/video/action.rs:218:VideoClient<'a>::coin_status | no_contract_match |
| src/video/action.rs:231:VideoClient<'a>::like | no_contract_match |
| src/video/action.rs:246:VideoClient<'a>::coin | no_contract_match |
| src/video/action.rs:258:VideoClient<'a>::favorite | no_contract_match |
| src/video/collection/action.rs:220:VideoClient<'a>::create_collection_series | no_contract_match, multipart |
| src/video/collection/action.rs:236:VideoClient<'a>::delete_collection_series | no_contract_match |
| src/video/collection/action.rs:250:VideoClient<'a>::delete_collection_archives | no_contract_match |
| src/video/collection/action.rs:265:VideoClient<'a>::add_collection_archives | no_contract_match |
| src/video/collection/action.rs:280:VideoClient<'a>::update_collection_series | no_contract_match, multipart |
| src/video/report.rs:54:VideoClient<'a>::report_watch_progress | no_contract_match, multipart |
| src/vip/action.rs:21:VipClient<'a>::receive_privilege | no_contract_match |
| src/vip/action.rs:35:VipClient<'a>::add_experience | no_contract_match |

## 局限

- Static declarations; compiler visibility and cfg selection are not evaluated.
- Macros are recorded but not expanded; const/import resolution is candidate evidence.
- Parameter expressions and Rust types are preserved, not translated or validated.
- request_shell_candidate does not mean fully auto-migratable or implemented.
- Contract fixtures are historical evidence; no live requests were made.
