"""EmojiPicker - 桌面 Emoji 选择器"""

import json
import os
import sys
from pathlib import Path
from PyQt6.QtCore import Qt, QSize, QSettings, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QIcon, QPainter, QLinearGradient,
    QClipboard, QAction, QPixmap, QFontDatabase, QCursor
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QScrollArea, QFrame, QGridLayout,
    QTabWidget, QComboBox, QToolTip, QSystemTrayIcon, QMenu,
    QMessageBox, QSizePolicy, QStyledItemDelegate, QStyle,
    QGraphicsDropShadowEffect, QStackedWidget, QToolButton
)

# ---------------------------------------------------------------------------
# Emoji database – a curated subset; easily extendable
# ---------------------------------------------------------------------------
EMOJI_DATA = {
    "😀": {"name": "笑脸", "keywords": ["smile", "happy", "face"], "category": "表情"},
    "😃": {"name": "大笑", "keywords": ["happy", "joy", "haha"], "category": "表情"},
    "😄": {"name": "笑眼", "keywords": ["happy", "laugh", "smile"], "category": "表情"},
    "😁": {"name": "露齿笑", "keywords": ["grin", "cheerful"], "category": "表情"},
    "😆": {"name": "眯眼笑", "keywords": ["laugh", "satisfied"], "category": "表情"},
    "😅": {"name": "苦笑", "keywords": ["sweat", "nervous"], "category": "表情"},
    "🤣": {"name": "笑翻", "keywords": ["rofl", "laugh"], "category": "表情"},
    "😂": {"name": "笑哭", "keywords": ["joy", "tears", "lol"], "category": "表情"},
    "🙂": {"name": "微笑", "keywords": ["smile", "slightly"], "category": "表情"},
    "🙃": {"name": "倒脸", "keywords": ["upside", "sarcasm"], "category": "表情"},
    "😉": {"name": "眨眼", "keywords": ["wink", "flirt"], "category": "表情"},
    "😊": {"name": "羞涩微笑", "keywords": ["blush", "happy"], "category": "表情"},
    "😇": {"name": "天使", "keywords": ["angel", "halo", "innocent"], "category": "表情"},
    "🥰": {"name": "爱心脸", "keywords": ["love", "hearts", "adore"], "category": "表情"},
    "😍": {"name": "花痴", "keywords": ["heart eyes", "love"], "category": "表情"},
    "🤩": {"name": "星星眼", "keywords": ["star", "excited", "wow"], "category": "表情"},
    "😘": {"name": "飞吻", "keywords": ["kiss", "love"], "category": "表情"},
    "😗": {"name": "亲亲", "keywords": ["kiss", "smooch"], "category": "表情"},
    "😚": {"name": "闭眼亲", "keywords": ["kiss", "blush"], "category": "表情"},
    "😙": {"name": "微笑亲", "keywords": ["kiss", "happy"], "category": "表情"},
    "🥲": {"name": "含泪微笑", "keywords": ["smile", "tear", "grateful"], "category": "表情"},
    "😋": {"name": "好吃", "keywords": ["yum", "delicious", "tongue"], "category": "表情"},
    "😛": {"name": "吐舌", "keywords": ["tongue", "playful"], "category": "表情"},
    "😜": {"name": "眨眼吐舌", "keywords": ["tongue", "wink", "crazy"], "category": "表情"},
    "🤪": {"name": "疯狂", "keywords": ["crazy", "wild", "zany"], "category": "表情"},
    "😝": {"name": "眯眼吐舌", "keywords": ["tongue", "squint"], "category": "表情"},
    "🤑": {"name": "财迷", "keywords": ["money", "rich", "dollar"], "category": "表情"},
    "🤗": {"name": "拥抱", "keywords": ["hug", "cuddle"], "category": "表情"},
    "🤭": {"name": "偷笑", "keywords": ["giggle", "oops"], "category": "表情"},
    "🤫": {"name": "嘘", "keywords": ["quiet", "shh", "secret"], "category": "表情"},
    "🤔": {"name": "思考", "keywords": ["think", "hmm"], "category": "表情"},
    "🫡": {"name": "敬礼", "keywords": ["salute", "respect"], "category": "表情"},
    "🤐": {"name": "拉链嘴", "keywords": ["zip", "quiet", "sealed"], "category": "表情"},
    "🫠": {"name": "融化", "keywords": ["melt", "hot"], "category": "表情"},
    "😐": {"name": "无语", "keywords": ["neutral", "meh"], "category": "表情"},
    "😑": {"name": "面无表情", "keywords": ["expressionless", "blank"], "category": "表情"},
    "😶": {"name": "沉默", "keywords": ["silent", "no mouth"], "category": "表情"},
    "🫥": {"name": "虚线脸", "keywords": ["invisible", "hidden"], "category": "表情"},
    "😏": {"name": "得意", "keywords": ["smirk", "sly"], "category": "表情"},
    "😒": {"name": "不高兴", "keywords": ["unamused", "annoyed"], "category": "表情"},
    "🙄": {"name": "翻白眼", "keywords": ["eye roll", "whatever"], "category": "表情"},
    "😬": {"name": "龇牙", "keywords": ["grimace", "awkward"], "category": "表情"},
    "😮‍💨": {"name": "叹气", "keywords": ["sigh", "exhale"], "category": "表情"},
    "🤥": {"name": "长鼻子", "keywords": ["lie", "pinocchio"], "category": "表情"},
    "🫨": {"name": "摇头", "keywords": ["shake", "shock"], "category": "表情"},
    "😌": {"name": "如释重负", "keywords": ["relieved", "peaceful"], "category": "表情"},
    "😔": {"name": "沉思", "keywords": ["sad", "pensive"], "category": "表情"},
    "😪": {"name": "困", "keywords": ["sleepy", "tired"], "category": "表情"},
    "🤤": {"name": "流口水", "keywords": ["drool", "yum"], "category": "表情"},
    "😴": {"name": "睡觉", "keywords": ["sleep", "zzz"], "category": "表情"},
    "😷": {"name": "口罩", "keywords": ["mask", "sick", "covid"], "category": "表情"},
    "🤒": {"name": "发烧", "keywords": ["sick", "fever", "thermometer"], "category": "表情"},
    "🤕": {"name": "受伤", "keywords": ["hurt", "bandage"], "category": "表情"},
    "🤢": {"name": "恶心", "keywords": ["nausea", "sick"], "category": "表情"},
    "🤮": {"name": "呕吐", "keywords": ["vomit", "puke"], "category": "表情"},
    "🥵": {"name": "热", "keywords": ["hot", "sweating"], "category": "表情"},
    "🥶": {"name": "冷", "keywords": ["cold", "freezing"], "category": "表情"},
    "🥴": {"name": "晕", "keywords": ["dizzy", "woozy"], "category": "表情"},
    "😵": {"name": "头晕", "keywords": ["dizzy", "dead"], "category": "表情"},
    "😵‍💫": {"name": "眼花", "keywords": ["spiral", "hypnotized"], "category": "表情"},
    "🤯": {"name": "爆炸头", "keywords": ["mind blown", "shock"], "category": "表情"},
    "🤠": {"name": "牛仔", "keywords": ["cowboy", "hat"], "category": "表情"},
    "🥳": {"name": "派对", "keywords": ["party", "celebrate"], "category": "表情"},
    "🥸": {"name": "伪装", "keywords": ["disguise", "glasses"], "category": "表情"},
    "😎": {"name": "墨镜", "keywords": ["cool", "sunglasses"], "category": "表情"},
    "🤓": {"name": "书呆子", "keywords": ["nerd", "geek"], "category": "表情"},
    "🧐": {"name": "单片眼镜", "keywords": ["monocle", "inspect"], "category": "表情"},
    "😕": {"name": "困惑", "keywords": ["confused", "hmm"], "category": "表情"},
    "🫤": {"name": "斜嘴", "keywords": ["skeptical", "meh"], "category": "表情"},
    "😟": {"name": "担心", "keywords": ["worried", "concern"], "category": "表情"},
    "🙁": {"name": "皱眉", "keywords": ["frown", "sad"], "category": "表情"},
    "☹️": {"name": "大皱眉", "keywords": ["frown", "upset"], "category": "表情"},
    "😮": {"name": "惊讶", "keywords": ["surprised", "open mouth"], "category": "表情"},
    "😯": {"name": "震惊", "keywords": ["hushed", "stunned"], "category": "表情"},
    "😲": {"name": "目瞪口呆", "keywords": ["astonished", "shock"], "category": "表情"},
    "😳": {"name": "脸红", "keywords": ["flushed", "embarrassed"], "category": "表情"},
    "🥺": {"name": "祈求", "keywords": ["pleading", "puppy eyes"], "category": "表情"},
    "🥹": {"name": "忍泪", "keywords": ["holding tears", "emotional"], "category": "表情"},
    "😦": {"name": "啊", "keywords": ["frown", "open mouth"], "category": "表情"},
    "😧": {"name": "痛苦", "keywords": ["anguished", "upset"], "category": "表情"},
    "😨": {"name": "害怕", "keywords": ["fearful", "scared"], "category": "表情"},
    "😰": {"name": "冷汗", "keywords": ["anxious", "sweat"], "category": "表情"},
    "😥": {"name": "失望但松口气", "keywords": ["sad", "relieved"], "category": "表情"},
    "😢": {"name": "哭", "keywords": ["cry", "tear"], "category": "表情"},
    "😭": {"name": "大哭", "keywords": ["sob", "wail"], "category": "表情"},
    "😱": {"name": "恐惧", "keywords": ["scream", "horror"], "category": "表情"},
    "😖": {"name": "困惑", "keywords": ["confounded", "frustrated"], "category": "表情"},
    "😣": {"name": "坚持", "keywords": ["persevere", "struggle"], "category": "表情"},
    "😞": {"name": "沮丧", "keywords": ["sad", "down"], "category": "表情"},
    "😓": {"name": "冷汗", "keywords": ["cold sweat", "hard work"], "category": "表情"},
    "😩": {"name": "疲惫", "keywords": ["weary", "tired"], "category": "表情"},
    "😫": {"name": "累", "keywords": ["tired", "exhausted"], "category": "表情"},
    "🥱": {"name": "打哈欠", "keywords": ["yawn", "bored"], "category": "表情"},
    "😤": {"name": "怒", "keywords": ["angry", "triumph"], "category": "表情"},
    "😡": {"name": "生气", "keywords": ["angry", "rage", "pout"], "category": "表情"},
    "😠": {"name": "愤怒", "keywords": ["angry", "mad"], "category": "表情"},
    "🤬": {"name": "骂人", "keywords": ["swear", "cursing"], "category": "表情"},
    "💀": {"name": "骷髅", "keywords": ["skull", "dead", "death"], "category": "表情"},
    "☠️": {"name": "骷髅交叉骨", "keywords": ["skull", "bones", "danger"], "category": "表情"},
    "💩": {"name": "便便", "keywords": ["poop", "poo"], "category": "表情"},
    "🤡": {"name": "小丑", "keywords": ["clown", "joke"], "category": "表情"},
    "👹": {"name": "鬼", "keywords": ["ogre", "monster"], "category": "表情"},
    "👺": {"name": "天狗", "keywords": ["goblin", "tengu"], "category": "表情"},
    "👻": {"name": "幽灵", "keywords": ["ghost", "spooky"], "category": "表情"},
    "👽": {"name": "外星人", "keywords": ["alien", "ufo"], "category": "表情"},
    "👾": {"name": "外星怪物", "keywords": ["alien", "game", "space invader"], "category": "表情"},
    "🤖": {"name": "机器人", "keywords": ["robot", "bot"], "category": "表情"},
    "😺": {"name": "猫笑", "keywords": ["cat", "smile"], "category": "表情"},
    "😸": {"name": "猫露齿笑", "keywords": ["cat", "grin"], "category": "表情"},
    "😹": {"name": "猫笑哭", "keywords": ["cat", "joy", "tears"], "category": "表情"},
    "😻": {"name": "猫花痴", "keywords": ["cat", "heart eyes", "love"], "category": "表情"},
    "😼": {"name": "猫冷笑", "keywords": ["cat", "smirk"], "category": "表情"},
    "😽": {"name": "猫亲亲", "keywords": ["cat", "kiss"], "category": "表情"},
    "🙀": {"name": "猫震惊", "keywords": ["cat", "shock", "weary"], "category": "表情"},
    "😿": {"name": "猫哭", "keywords": ["cat", "cry", "sad"], "category": "表情"},
    "😾": {"name": "猫生气", "keywords": ["cat", "angry", "pout"], "category": "表情"},
    "❤️": {"name": "红心", "keywords": ["heart", "love", "red"], "category": "表情"},
    "🧡": {"name": "橙心", "keywords": ["heart", "orange"], "category": "表情"},
    "💛": {"name": "黄心", "keywords": ["heart", "yellow"], "category": "表情"},
    "💚": {"name": "绿心", "keywords": ["heart", "green"], "category": "表情"},
    "💙": {"name": "蓝心", "keywords": ["heart", "blue"], "category": "表情"},
    "💜": {"name": "紫心", "keywords": ["heart", "purple"], "category": "表情"},
    "🤎": {"name": "棕心", "keywords": ["heart", "brown"], "category": "表情"},
    "🖤": {"name": "黑心", "keywords": ["heart", "black"], "category": "表情"},
    "🤍": {"name": "白心", "keywords": ["heart", "white"], "category": "表情"},
    "💔": {"name": "碎心", "keywords": ["heart", "broken"], "category": "表情"},
    "💕": {"name": "两心", "keywords": ["hearts", "love"], "category": "表情"},
    "💞": {"name": "旋转心", "keywords": ["hearts", "revolving"], "category": "表情"},
    "💓": {"name": "心跳", "keywords": ["heart", "beat", "pulse"], "category": "表情"},
    "💗": {"name": "成长心", "keywords": ["heart", "growing"], "category": "表情"},
    "💖": {"name": "闪亮心", "keywords": ["heart", "sparkle"], "category": "表情"},
    "💘": {"name": "箭穿心", "keywords": ["heart", "arrow", "cupid"], "category": "表情"},
    "💝": {"name": "礼盒心", "keywords": ["heart", "ribbon", "gift"], "category": "表情"},
    "💟": {"name": "装饰心", "keywords": ["heart", "decoration"], "category": "表情"},
    "👋": {"name": "挥手", "keywords": ["wave", "hello", "bye"], "category": "手势"},
    "🤚": {"name": "手背", "keywords": ["hand", "raised", "back"], "category": "手势"},
    "🖐️": {"name": "张开手", "keywords": ["hand", "fingers", "splay"], "category": "手势"},
    "✋": {"name": "举手", "keywords": ["hand", "stop", "high five"], "category": "手势"},
    "🖖": {"name": "瓦肯举手礼", "keywords": ["spock", "vulcan"], "category": "手势"},
    "🫱": {"name": "右手", "keywords": ["hand", "right", "palm"], "category": "手势"},
    "🫲": {"name": "左手", "keywords": ["hand", "left", "palm"], "category": "手势"},
    "🫳": {"name": "手掌朝下", "keywords": ["hand", "down", "palm"], "category": "手势"},
    "🫴": {"name": "手掌朝上", "keywords": ["hand", "up", "palm"], "category": "手势"},
    "👌": {"name": "OK", "keywords": ["ok", "perfect", "okay"], "category": "手势"},
    "🤌": {"name": "捏手指", "keywords": ["pinch", "italian"], "category": "手势"},
    "🤏": {"name": "捏", "keywords": ["pinch", "small", "tiny"], "category": "手势"},
    "✌️": {"name": "胜利", "keywords": ["peace", "victory"], "category": "手势"},
    "🤞": {"name": "交叉手指", "keywords": ["cross", "fingers", "luck"], "category": "手势"},
    "🫰": {"name": "弹指", "keywords": ["snap", "money"], "category": "手势"},
    "🤟": {"name": "爱你", "keywords": ["love", "ily"], "category": "手势"},
    "🤘": {"name": "摇滚", "keywords": ["rock", "metal", "horns"], "category": "手势"},
    "👈": {"name": "向左指", "keywords": ["point", "left"], "category": "手势"},
    "👉": {"name": "向右指", "keywords": ["point", "right"], "category": "手势"},
    "👆": {"name": "向上指", "keywords": ["point", "up"], "category": "手势"},
    "🖕": {"name": "竖中指", "keywords": ["middle finger", "flip"], "category": "手势"},
    "👇": {"name": "向下指", "keywords": ["point", "down"], "category": "手势"},
    "☝️": {"name": "食指朝上", "keywords": ["point", "up", "index"], "category": "手势"},
    "👍": {"name": "赞", "keywords": ["thumbs up", "like", "yes"], "category": "手势"},
    "👎": {"name": "踩", "keywords": ["thumbs down", "dislike", "no"], "category": "手势"},
    "✊": {"name": "举起拳头", "keywords": ["fist", "punch", "power"], "category": "手势"},
    "👊": {"name": "出拳", "keywords": ["fist", "punch", "hit"], "category": "手势"},
    "🤛": {"name": "左拳", "keywords": ["fist", "left", "bump"], "category": "手势"},
    "🤜": {"name": "右拳", "keywords": ["fist", "right", "bump"], "category": "手势"},
    "👏": {"name": "鼓掌", "keywords": ["clap", "applause"], "category": "手势"},
    "🙌": {"name": "举双手", "keywords": ["hooray", "celebrate"], "category": "手势"},
    "🫶": {"name": "双手比心", "keywords": ["heart", "hands", "love"], "category": "手势"},
    "👐": {"name": "张开双手", "keywords": ["hands", "open"], "category": "手势"},
    "🤲": {"name": "掌心向上", "keywords": ["palms", "cupped"], "category": "手势"},
    "🤝": {"name": "握手", "keywords": ["handshake", "deal"], "category": "手势"},
    "🙏": {"name": "合十", "keywords": ["pray", "thanks", "please"], "category": "手势"},
    "🐶": {"name": "狗", "keywords": ["dog", "puppy"], "category": "动物"},
    "🐱": {"name": "猫", "keywords": ["cat", "kitten"], "category": "动物"},
    "🐭": {"name": "老鼠", "keywords": ["mouse"], "category": "动物"},
    "🐹": {"name": "仓鼠", "keywords": ["hamster"], "category": "动物"},
    "🐰": {"name": "兔子", "keywords": ["rabbit", "bunny"], "category": "动物"},
    "🦊": {"name": "狐狸", "keywords": ["fox"], "category": "动物"},
    "🐻": {"name": "熊", "keywords": ["bear"], "category": "动物"},
    "🐼": {"name": "熊猫", "keywords": ["panda"], "category": "动物"},
    "🐨": {"name": "考拉", "keywords": ["koala"], "category": "动物"},
    "🐯": {"name": "老虎", "keywords": ["tiger"], "category": "动物"},
    "🦁": {"name": "狮子", "keywords": ["lion"], "category": "动物"},
    "🐮": {"name": "牛", "keywords": ["cow"], "category": "动物"},
    "🐷": {"name": "猪", "keywords": ["pig"], "category": "动物"},
    "🐸": {"name": "青蛙", "keywords": ["frog"], "category": "动物"},
    "🐵": {"name": "猴子", "keywords": ["monkey"], "category": "动物"},
    "🙈": {"name": "非礼勿视", "keywords": ["monkey", "see no evil"], "category": "动物"},
    "🙉": {"name": "非礼勿听", "keywords": ["monkey", "hear no evil"], "category": "动物"},
    "🙊": {"name": "非礼勿言", "keywords": ["monkey", "speak no evil"], "category": "动物"},
    "🐔": {"name": "鸡", "keywords": ["chicken"], "category": "动物"},
    "🐧": {"name": "企鹅", "keywords": ["penguin"], "category": "动物"},
    "🐦": {"name": "鸟", "keywords": ["bird"], "category": "动物"},
    "🐤": {"name": "小鸡", "keywords": ["chick", "baby"], "category": "动物"},
    "🦆": {"name": "鸭子", "keywords": ["duck"], "category": "动物"},
    "🦅": {"name": "鹰", "keywords": ["eagle"], "category": "动物"},
    "🦉": {"name": "猫头鹰", "keywords": ["owl"], "category": "动物"},
    "🦇": {"name": "蝙蝠", "keywords": ["bat"], "category": "动物"},
    "🐺": {"name": "狼", "keywords": ["wolf"], "category": "动物"},
    "🐗": {"name": "野猪", "keywords": ["boar"], "category": "动物"},
    "🐴": {"name": "马", "keywords": ["horse"], "category": "动物"},
    "🦄": {"name": "独角兽", "keywords": ["unicorn"], "category": "动物"},
    "🐝": {"name": "蜜蜂", "keywords": ["bee", "honey"], "category": "动物"},
    "🪱": {"name": "虫子", "keywords": ["worm"], "category": "动物"},
    "🐛": {"name": "毛毛虫", "keywords": ["bug", "caterpillar"], "category": "动物"},
    "🦋": {"name": "蝴蝶", "keywords": ["butterfly"], "category": "动物"},
    "🐌": {"name": "蜗牛", "keywords": ["snail"], "category": "动物"},
    "🐞": {"name": "瓢虫", "keywords": ["ladybug", "beetle"], "category": "动物"},
    "🐜": {"name": "蚂蚁", "keywords": ["ant"], "category": "动物"},
    "🪰": {"name": "苍蝇", "keywords": ["fly"], "category": "动物"},
    "🪲": {"name": "甲虫", "keywords": ["beetle"], "category": "动物"},
    "🪳": {"name": "蟑螂", "keywords": ["cockroach"], "category": "动物"},
    "🦟": {"name": "蚊子", "keywords": ["mosquito"], "category": "动物"},
    "🦗": {"name": "蟋蟀", "keywords": ["cricket"], "category": "动物"},
    "🕷️": {"name": "蜘蛛", "keywords": ["spider"], "category": "动物"},
    "🐢": {"name": "乌龟", "keywords": ["turtle", "tortoise"], "category": "动物"},
    "🐍": {"name": "蛇", "keywords": ["snake"], "category": "动物"},
    "🦎": {"name": "蜥蜴", "keywords": ["lizard"], "category": "动物"},
    "🦖": {"name": "霸王龙", "keywords": ["t-rex", "dinosaur"], "category": "动物"},
    "🦕": {"name": "蜥脚恐龙", "keywords": ["dinosaur", "brontosaurus"], "category": "动物"},
    "🐙": {"name": "章鱼", "keywords": ["octopus"], "category": "动物"},
    "🦑": {"name": "鱿鱼", "keywords": ["squid"], "category": "动物"},
    "🦐": {"name": "虾", "keywords": ["shrimp"], "category": "动物"},
    "🦞": {"name": "龙虾", "keywords": ["lobster"], "category": "动物"},
    "🦀": {"name": "螃蟹", "keywords": ["crab"], "category": "动物"},
    "🐡": {"name": "河豚", "keywords": ["puffer", "fish"], "category": "动物"},
    "🐠": {"name": "热带鱼", "keywords": ["fish", "tropical"], "category": "动物"},
    "🐟": {"name": "鱼", "keywords": ["fish"], "category": "动物"},
    "🐬": {"name": "海豚", "keywords": ["dolphin"], "category": "动物"},
    "🐳": {"name": "喷水鲸", "keywords": ["whale", "spouting"], "category": "动物"},
    "🐋": {"name": "鲸鱼", "keywords": ["whale"], "category": "动物"},
    "🦈": {"name": "鲨鱼", "keywords": ["shark"], "category": "动物"},
    "🦭": {"name": "海豹", "keywords": ["seal"], "category": "动物"},
    "🐊": {"name": "鳄鱼", "keywords": ["crocodile", "alligator"], "category": "动物"},
    "🐘": {"name": "大象", "keywords": ["elephant"], "category": "动物"},
    "🦛": {"name": "河马", "keywords": ["hippo"], "category": "动物"},
    "🦏": {"name": "犀牛", "keywords": ["rhino"], "category": "动物"},
    "🐪": {"name": "骆驼", "keywords": ["camel"], "category": "动物"},
    "🐫": {"name": "双峰驼", "keywords": ["camel", "two humps"], "category": "动物"},
    "🦒": {"name": "长颈鹿", "keywords": ["giraffe"], "category": "动物"},
    "🦘": {"name": "袋鼠", "keywords": ["kangaroo"], "category": "动物"},
    "🦬": {"name": "野牛", "keywords": ["bison"], "category": "动物"},
    "🐃": {"name": "水牛", "keywords": ["water buffalo"], "category": "动物"},
    "🐎": {"name": "赛马", "keywords": ["horse", "race"], "category": "动物"},
    "🐖": {"name": "猪", "keywords": ["pig"], "category": "动物"},
    "🐑": {"name": "羊", "keywords": ["sheep", "ewe"], "category": "动物"},
    "🦙": {"name": "羊驼", "keywords": ["llama", "alpaca"], "category": "动物"},
    "🐐": {"name": "山羊", "keywords": ["goat"], "category": "动物"},
    "🦌": {"name": "鹿", "keywords": ["deer"], "category": "动物"},
    "🐕": {"name": "狗", "keywords": ["dog"], "category": "动物"},
    "🐩": {"name": "贵宾犬", "keywords": ["poodle"], "category": "动物"},
    "🦮": {"name": "导盲犬", "keywords": ["guide dog"], "category": "动物"},
    "🐕‍🦺": {"name": "服务犬", "keywords": ["service dog"], "category": "动物"},
    "🐈": {"name": "猫", "keywords": ["cat"], "category": "动物"},
    "🐈‍⬛": {"name": "黑猫", "keywords": ["black cat"], "category": "动物"},
    "🪶": {"name": "羽毛", "keywords": ["feather"], "category": "动物"},
    "🐓": {"name": "公鸡", "keywords": ["rooster"], "category": "动物"},
    "🦃": {"name": "火鸡", "keywords": ["turkey"], "category": "动物"},
    "🦤": {"name": "渡渡鸟", "keywords": ["dodo"], "category": "动物"},
    "🦜": {"name": "鹦鹉", "keywords": ["parrot"], "category": "动物"},
    "🦢": {"name": "天鹅", "keywords": ["swan"], "category": "动物"},
    "🦩": {"name": "火烈鸟", "keywords": ["flamingo"], "category": "动物"},
    "🕊️": {"name": "鸽子", "keywords": ["dove", "peace"], "category": "动物"},
    "🐇": {"name": "兔子", "keywords": ["rabbit"], "category": "动物"},
    "🦝": {"name": "浣熊", "keywords": ["raccoon"], "category": "动物"},
    "🦨": {"name": "臭鼬", "keywords": ["skunk"], "category": "动物"},
    "🦡": {"name": "獾", "keywords": ["badger"], "category": "动物"},
    "🦫": {"name": "海狸", "keywords": ["beaver"], "category": "动物"},
    "🦦": {"name": "水獭", "keywords": ["otter"], "category": "动物"},
    "🦥": {"name": "树懒", "keywords": ["sloth"], "category": "动物"},
    "🐁": {"name": "老鼠", "keywords": ["mouse"], "category": "动物"},
    "🐀": {"name": "大鼠", "keywords": ["rat"], "category": "动物"},
    "🐿️": {"name": "松鼠", "keywords": ["squirrel"], "category": "动物"},
    "🦔": {"name": "刺猬", "keywords": ["hedgehog"], "category": "动物"},
    "🐾": {"name": "爪印", "keywords": ["paw", "print"], "category": "动物"},
    "🐉": {"name": "龙", "keywords": ["dragon"], "category": "动物"},
    "🐲": {"name": "龙头", "keywords": ["dragon", "face"], "category": "动物"},
    "🌵": {"name": "仙人掌", "keywords": ["cactus"], "category": "动物"},
    "🎄": {"name": "圣诞树", "keywords": ["christmas", "tree"], "category": "动物"},
    "🌲": {"name": "松树", "keywords": ["pine", "tree", "evergreen"], "category": "动物"},
    "🌳": {"name": "落叶树", "keywords": ["tree", "deciduous"], "category": "动物"},
    "🌴": {"name": "棕榈树", "keywords": ["palm", "tree"], "category": "动物"},
    "🪵": {"name": "木头", "keywords": ["wood", "log"], "category": "动物"},
    "🌱": {"name": "幼苗", "keywords": ["seedling", "sprout"], "category": "动物"},
    "🌿": {"name": "草药", "keywords": ["herb", "leaf"], "category": "动物"},
    "☘️": {"name": "三叶草", "keywords": ["shamrock", "clover"], "category": "动物"},
    "🍀": {"name": "四叶草", "keywords": ["four leaf", "luck"], "category": "动物"},
    "🎍": {"name": "松竹", "keywords": ["bamboo", "pine"], "category": "动物"},
    "🪴": {"name": "盆栽", "keywords": ["potted plant"], "category": "动物"},
    "🌾": {"name": "稻穗", "keywords": ["rice", "ear"], "category": "动物"},
    "🌺": {"name": "木槿", "keywords": ["hibiscus", "flower"], "category": "动物"},
    "🌻": {"name": "向日葵", "keywords": ["sunflower"], "category": "动物"},
    "🌹": {"name": "玫瑰", "keywords": ["rose"], "category": "动物"},
    "🥀": {"name": "枯萎的花", "keywords": ["wilted", "flower"], "category": "动物"},
    "🌷": {"name": "郁金香", "keywords": ["tulip"], "category": "动物"},
    "🌸": {"name": "樱花", "keywords": ["cherry blossom", "sakura"], "category": "动物"},
    "💐": {"name": "花束", "keywords": ["bouquet", "flowers"], "category": "动物"},
    "🍎": {"name": "红苹果", "keywords": ["apple", "red"], "category": "食物"},
    "🍐": {"name": "梨", "keywords": ["pear"], "category": "食物"},
    "🍊": {"name": "橘子", "keywords": ["tangerine", "orange"], "category": "食物"},
    "🍋": {"name": "柠檬", "keywords": ["lemon"], "category": "食物"},
    "🍌": {"name": "香蕉", "keywords": ["banana"], "category": "食物"},
    "🍉": {"name": "西瓜", "keywords": ["watermelon"], "category": "食物"},
    "🍇": {"name": "葡萄", "keywords": ["grapes"], "category": "食物"},
    "🍓": {"name": "草莓", "keywords": ["strawberry"], "category": "食物"},
    "🫐": {"name": "蓝莓", "keywords": ["blueberry"], "category": "食物"},
    "🍈": {"name": "甜瓜", "keywords": ["melon"], "category": "食物"},
    "🍒": {"name": "樱桃", "keywords": ["cherry"], "category": "食物"},
    "🍑": {"name": "桃子", "keywords": ["peach"], "category": "食物"},
    "🥭": {"name": "芒果", "keywords": ["mango"], "category": "食物"},
    "🍍": {"name": "菠萝", "keywords": ["pineapple"], "category": "食物"},
    "🥥": {"name": "椰子", "keywords": ["coconut"], "category": "食物"},
    "🥝": {"name": "猕猴桃", "keywords": ["kiwi"], "category": "食物"},
    "🍅": {"name": "番茄", "keywords": ["tomato"], "category": "食物"},
    "🍆": {"name": "茄子", "keywords": ["eggplant", "aubergine"], "category": "食物"},
    "🥑": {"name": "牛油果", "keywords": ["avocado"], "category": "食物"},
    "🫛": {"name": "豌豆荚", "keywords": ["pea", "pod"], "category": "食物"},
    "🥦": {"name": "西兰花", "keywords": ["broccoli"], "category": "食物"},
    "🥬": {"name": "绿叶菜", "keywords": ["leafy", "green"], "category": "食物"},
    "黄瓜": {"name": "黄瓜", "keywords": ["cucumber"], "category": "食物"},
    "🌶️": {"name": "辣椒", "keywords": ["pepper", "hot", "spicy"], "category": "食物"},
    "🫑": {"name": "青椒", "keywords": ["pepper", "bell"], "category": "食物"},
    "🌽": {"name": "玉米", "keywords": ["corn"], "category": "食物"},
    "🥕": {"name": "胡萝卜", "keywords": ["carrot"], "category": "食物"},
    "🫒": {"name": "橄榄", "keywords": ["olive"], "category": "食物"},
    "🧄": {"name": "大蒜", "keywords": ["garlic"], "category": "食物"},
    "🧅": {"name": "洋葱", "keywords": ["onion"], "category": "食物"},
    "🥔": {"name": "土豆", "keywords": ["potato"], "category": "食物"},
    "🍠": {"name": "烤红薯", "keywords": ["sweet potato", "yam"], "category": "食物"},
    "🍞": {"name": "面包", "keywords": ["bread"], "category": "食物"},
    "🥐": {"name": "牛角面包", "keywords": ["croissant"], "category": "食物"},
    "🥖": {"name": "法棍", "keywords": ["baguette", "bread"], "category": "食物"},
    "🫓": {"name": "扁面包", "keywords": ["flatbread"], "category": "食物"},
    "🥨": {"name": "椒盐卷饼", "keywords": ["pretzel"], "category": "食物"},
    "🥯": {"name": "百吉饼", "keywords": ["bagel"], "category": "食物"},
    "🥞": {"name": "煎饼", "keywords": ["pancake"], "category": "食物"},
    "🧇": {"name": "华夫饼", "keywords": ["waffle"], "category": "食物"},
    "🧀": {"name": "奶酪", "keywords": ["cheese"], "category": "食物"},
    "🍖": {"name": "肉", "keywords": ["meat", "bone"], "category": "食物"},
    "🍗": {"name": "鸡腿", "keywords": ["chicken", "leg"], "category": "食物"},
    "🥩": {"name": "牛排", "keywords": ["steak", "meat"], "category": "食物"},
    "🥓": {"name": "培根", "keywords": ["bacon"], "category": "食物"},
    "🍔": {"name": "汉堡", "keywords": ["burger", "hamburger"], "category": "食物"},
    "🍟": {"name": "薯条", "keywords": ["fries", "chips"], "category": "食物"},
    "🍕": {"name": "披萨", "keywords": ["pizza"], "category": "食物"},
    "🌭": {"name": "热狗", "keywords": ["hotdog", "sausage"], "category": "食物"},
    "🥪": {"name": "三明治", "keywords": ["sandwich"], "category": "食物"},
    "🌮": {"name": "墨西哥卷", "keywords": ["taco"], "category": "食物"},
    "🌯": {"name": "墨西哥卷饼", "keywords": ["burrito", "wrap"], "category": "食物"},
    "🫔": {"name": "粽子", "keywords": ["tamale"], "category": "食物"},
    "🥙": {"name": "皮塔饼", "keywords": ["pita", "falafel"], "category": "食物"},
    "🧆": {"name": "炸豆丸子", "keywords": ["falafel"], "category": "食物"},
    "🥚": {"name": "蛋", "keywords": ["egg"], "category": "食物"},
    "🍳": {"name": "煎蛋", "keywords": ["egg", "frying", "cook"], "category": "食物"},
    "🥘": {"name": "浅锅", "keywords": ["pan", "cooking"], "category": "食物"},
    "🍲": {"name": "火锅", "keywords": ["pot", "stew"], "category": "食物"},
    "🫕": {"name": "奶酪火锅", "keywords": ["fondue"], "category": "食物"},
    "🥣": {"name": "碗", "keywords": ["bowl", "porridge"], "category": "食物"},
    "🥗": {"name": "沙拉", "keywords": ["salad", "green"], "category": "食物"},
    "🍿": {"name": "爆米花", "keywords": ["popcorn"], "category": "食物"},
    "🧈": {"name": "黄油", "keywords": ["butter"], "category": "食物"},
    "🧂": {"name": "盐", "keywords": ["salt"], "category": "食物"},
    "🥫": {"name": "罐头", "keywords": ["can", "food"], "category": "食物"},
    "🍱": {"name": "便当", "keywords": ["bento", "box"], "category": "食物"},
    "🍘": {"name": "米饼", "keywords": ["rice cracker"], "category": "食物"},
    "🍙": {"name": "饭团", "keywords": ["rice ball"], "category": "食物"},
    "🍚": {"name": "米饭", "keywords": ["rice", "cooked"], "category": "食物"},
    "🍛": {"name": "咖喱饭", "keywords": ["curry", "rice"], "category": "食物"},
    "🍜": {"name": "面条", "keywords": ["noodles", "ramen"], "category": "食物"},
    "🍝": {"name": "意面", "keywords": ["pasta", "spaghetti"], "category": "食物"},
    "🍠": {"name": "烤红薯", "keywords": ["sweet potato"], "category": "食物"},
    "🍢": {"name": "关东煮", "keywords": ["oden", "skewer"], "category": "食物"},
    "🍣": {"name": "寿司", "keywords": ["sushi"], "category": "食物"},
    "🍤": {"name": "炸虾", "keywords": ["shrimp", "tempura"], "category": "食物"},
    "🍥": {"name": "鱼饼", "keywords": ["fish cake"], "category": "食物"},
    "🥮": {"name": "月饼", "keywords": ["mooncake"], "category": "食物"},
    "🍡": {"name": "团子", "keywords": ["dango"], "category": "食物"},
    "🥟": {"name": "饺子", "keywords": ["dumpling"], "category": "食物"},
    "🥠": {"name": "幸运饼干", "keywords": ["fortune cookie"], "category": "食物"},
    "🥡": {"name": "外卖盒", "keywords": ["takeout", "box"], "category": "食物"},
    "🦀": {"name": "螃蟹", "keywords": ["crab"], "category": "食物"},
    "🍦": {"name": "冰淇淋", "keywords": ["ice cream", "soft"], "category": "食物"},
    "🍧": {"name": "刨冰", "keywords": ["shaved ice"], "category": "食物"},
    "🍨": {"name": "冰淇淋", "keywords": ["ice cream"], "category": "食物"},
    "🍩": {"name": "甜甜圈", "keywords": ["donut", "doughnut"], "category": "食物"},
    "🍪": {"name": "饼干", "keywords": ["cookie"], "category": "食物"},
    "🎂": {"name": "生日蛋糕", "keywords": ["birthday", "cake"], "category": "食物"},
    "🍰": {"name": "蛋糕", "keywords": ["cake", "shortcake"], "category": "食物"},
    "🧁": {"name": "纸杯蛋糕", "keywords": ["cupcake"], "category": "食物"},
    "🥧": {"name": "派", "keywords": ["pie"], "category": "食物"},
    "🍫": {"name": "巧克力", "keywords": ["chocolate"], "category": "食物"},
    "🍬": {"name": "糖果", "keywords": ["candy", "sweet"], "category": "食物"},
    "🍭": {"name": "棒棒糖", "keywords": ["lollipop", "candy"], "category": "食物"},
    "🍮": {"name": "布丁", "keywords": ["pudding", "custard"], "category": "食物"},
    "🍯": {"name": "蜂蜜", "keywords": ["honey", "pot"], "category": "食物"},
    "🍼": {"name": "奶瓶", "keywords": ["baby bottle", "milk"], "category": "食物"},
    "🥛": {"name": "牛奶", "keywords": ["milk", "glass"], "category": "食物"},
    "☕": {"name": "咖啡", "keywords": ["coffee", "hot"], "category": "食物"},
    "🫖": {"name": "茶壶", "keywords": ["teapot"], "category": "食物"},
    "🍵": {"name": "茶", "keywords": ["tea", "green"], "category": "食物"},
    "🧃": {"name": "果汁盒", "keywords": ["juice box"], "category": "食物"},
    "🥤": {"name": "饮料", "keywords": ["drink", "cup", "soda"], "category": "食物"},
    "🧋": {"name": "珍珠奶茶", "keywords": ["bubble tea", "boba"], "category": "食物"},
    "🍶": {"name": "清酒", "keywords": ["sake"], "category": "食物"},
    "🍺": {"name": "啤酒", "keywords": ["beer"], "category": "食物"},
    "🍻": {"name": "干杯", "keywords": ["beer", "cheers"], "category": "食物"},
    "🥂": {"name": "香槟干杯", "keywords": ["champagne", "cheers"], "category": "食物"},
    "🍷": {"name": "红酒", "keywords": ["wine", "red"], "category": "食物"},
    "🥃": {"name": "威士忌", "keywords": ["whiskey", "glass"], "category": "食物"},
    "🍸": {"name": "鸡尾酒", "keywords": ["cocktail", "martini"], "category": "食物"},
    "🍹": {"name": "热带饮品", "keywords": ["tropical", "drink"], "category": "食物"},
    "🧉": {"name": "马黛茶", "keywords": ["mate", "tea"], "category": "食物"},
    "🍾": {"name": "开香槟", "keywords": ["champagne", "celebrate"], "category": "食物"},
    "⚽": {"name": "足球", "keywords": ["soccer", "football"], "category": "活动"},
    "🏀": {"name": "篮球", "keywords": ["basketball"], "category": "活动"},
    "🏈": {"name": "橄榄球", "keywords": ["football", "american"], "category": "活动"},
    "⚾": {"name": "棒球", "keywords": ["baseball"], "category": "活动"},
    "🥎": {"name": "垒球", "keywords": ["softball"], "category": "活动"},
    "🎾": {"name": "网球", "keywords": ["tennis"], "category": "活动"},
    "🏐": {"name": "排球", "keywords": ["volleyball"], "category": "活动"},
    "🏉": {"name": "橄榄球", "keywords": ["rugby"], "category": "活动"},
    "🥏": {"name": "飞盘", "keywords": ["frisbee"], "category": "活动"},
    "🎱": {"name": "台球", "keywords": ["billiards", "pool", "8 ball"], "category": "活动"},
    "🪀": {"name": "悠悠球", "keywords": ["yo-yo"], "category": "活动"},
    "🏓": {"name": "乒乓球", "keywords": ["ping pong", "table tennis"], "category": "活动"},
    "🏸": {"name": "羽毛球", "keywords": ["badminton"], "category": "活动"},
    "🏒": {"name": "冰球", "keywords": ["hockey", "ice"], "category": "活动"},
    "🏑": {"name": "曲棍球", "keywords": ["hockey", "field"], "category": "活动"},
    "🥍": {"name": "长曲棍球", "keywords": ["lacrosse"], "category": "活动"},
    "🏏": {"name": "板球", "keywords": ["cricket"], "category": "活动"},
    "🪃": {"name": "回旋镖", "keywords": ["boomerang"], "category": "活动"},
    "🥅": {"name": "球门", "keywords": ["goal", "net"], "category": "活动"},
    "⛳": {"name": "高尔夫", "keywords": ["golf", "flag"], "category": "活动"},
    "🪁": {"name": "风筝", "keywords": ["kite"], "category": "活动"},
    "🏹": {"name": "弓箭", "keywords": ["archery", "bow"], "category": "活动"},
    "🎣": {"name": "钓鱼", "keywords": ["fishing", "rod"], "category": "活动"},
    "🤿": {"name": "潜水镜", "keywords": ["diving", "snorkel"], "category": "活动"},
    "🥊": {"name": "拳击手套", "keywords": ["boxing", "glove"], "category": "活动"},
    "🥋": {"name": "武术服", "keywords": ["martial arts", "karate"], "category": "活动"},
    "🎽": {"name": "运动服", "keywords": ["running", "shirt"], "category": "活动"},
    "🛹": {"name": "滑板", "keywords": ["skateboard"], "category": "活动"},
    "🛼": {"name": "溜冰鞋", "keywords": ["roller skate"], "category": "活动"},
    "⛸️": {"name": "冰鞋", "keywords": ["ice skate"], "category": "活动"},
    "🥌": {"name": "冰壶", "keywords": ["curling"], "category": "活动"},
    "🎿": {"name": "滑雪", "keywords": ["ski", "snow"], "category": "活动"},
    "🛷": {"name": "雪橇", "keywords": ["sled", "sledge"], "category": "活动"},
    "🥏": {"name": "飞盘", "keywords": ["frisbee", "disc"], "category": "活动"},
    "🎯": {"name": "靶心", "keywords": ["bullseye", "target", "dart"], "category": "活动"},
    "🎮": {"name": "游戏手柄", "keywords": ["game", "controller"], "category": "活动"},
    "🕹️": {"name": "摇杆", "keywords": ["joystick", "arcade"], "category": "活动"},
    "🎰": {"name": "老虎机", "keywords": ["slot machine", "casino"], "category": "活动"},
    "🎲": {"name": "骰子", "keywords": ["dice", "game"], "category": "活动"},
    "🧩": {"name": "拼图", "keywords": ["puzzle", "piece"], "category": "活动"},
    "🧸": {"name": "泰迪熊", "keywords": ["teddy bear", "toy"], "category": "活动"},
    "🪅": {"name": "彩罐", "keywords": ["pinata"], "category": "活动"},
    "🪆": {"name": "套娃", "keywords": ["matryoshka", "nesting dolls"], "category": "活动"},
    "♠️": {"name": "黑桃", "keywords": ["spade", "card"], "category": "活动"},
    "♥️": {"name": "红心", "keywords": ["heart", "card"], "category": "活动"},
    "♦️": {"name": "方块", "keywords": ["diamond", "card"], "category": "活动"},
    "♣️": {"name": "梅花", "keywords": ["club", "card"], "category": "活动"},
    "♟️": {"name": "兵", "keywords": ["chess", "pawn"], "category": "活动"},
    "🃏": {"name": "大小王", "keywords": ["joker", "wild"], "category": "活动"},
    "🀄": {"name": "麻将", "keywords": ["mahjong", "tile"], "category": "活动"},
    "🎴": {"name": "花牌", "keywords": ["flower card"], "category": "活动"},
    "🎭": {"name": "表演艺术", "keywords": ["performing arts", "theater"], "category": "活动"},
    "🎨": {"name": "调色板", "keywords": ["art", "paint", "palette"], "category": "活动"},
    "🧵": {"name": "线", "keywords": ["thread", "sewing"], "category": "活动"},
    "🧶": {"name": "毛线", "keywords": ["yarn", "knit"], "category": "活动"},
    "🎭": {"name": "面具", "keywords": ["mask", "theater", "drama"], "category": "活动"},
    "🎤": {"name": "麦克风", "keywords": ["microphone", "karaoke"], "category": "活动"},
    "🎧": {"name": "耳机", "keywords": ["headphones", "music"], "category": "活动"},
    "🎼": {"name": "乐谱", "keywords": ["music", "score"], "category": "活动"},
    "🎹": {"name": "钢琴", "keywords": ["piano", "keyboard"], "category": "活动"},
    "🥁": {"name": "鼓", "keywords": ["drum"], "category": "活动"},
    "🪘": {"name": "鼓", "keywords": ["drum", "bongo"], "category": "活动"},
    "🎷": {"name": "萨克斯", "keywords": ["saxophone"], "category": "活动"},
    "🎺": {"name": "小号", "keywords": ["trumpet", "horn"], "category": "活动"},
    "🎸": {"name": "吉他", "keywords": ["guitar"], "category": "活动"},
    "🪕": {"name": "班卓琴", "keywords": ["banjo"], "category": "活动"},
    "🎻": {"name": "小提琴", "keywords": ["violin"], "category": "活动"},
    "🎬": {"name": "场记板", "keywords": ["movie", "film", "clapper"], "category": "活动"},
    "🏆": {"name": "奖杯", "keywords": ["trophy", "winner", "champion"], "category": "活动"},
    "🏅": {"name": "奖牌", "keywords": ["medal", "sports"], "category": "活动"},
    "🥇": {"name": "金牌", "keywords": ["gold", "first", "medal"], "category": "活动"},
    "🥈": {"name": "银牌", "keywords": ["silver", "second", "medal"], "category": "活动"},
    "🥉": {"name": "铜牌", "keywords": ["bronze", "third", "medal"], "category": "活动"},
    "🎖️": {"name": "军功章", "keywords": ["medal", "military"], "category": "活动"},
    "🎗️": {"name": "丝带", "keywords": ["ribbon", "awareness"], "category": "活动"},
    "🎫": {"name": "门票", "keywords": ["ticket", "admission"], "category": "活动"},
    "🎟️": {"name": "入场券", "keywords": ["ticket", "event"], "category": "活动"},
    "🎪": {"name": "马戏团", "keywords": ["circus", "tent"], "category": "活动"},
    "✈️": {"name": "飞机", "keywords": ["airplane", "plane", "fly"], "category": "旅行"},
    "🚀": {"name": "火箭", "keywords": ["rocket", "space"], "category": "旅行"},
    "🛸": {"name": "飞碟", "keywords": ["ufo", "flying saucer"], "category": "旅行"},
    "🚁": {"name": "直升机", "keywords": ["helicopter"], "category": "旅行"},
    "⛵": {"name": "帆船", "keywords": ["sailboat", "boat"], "category": "旅行"},
    "🚢": {"name": "轮船", "keywords": ["ship", "cruise"], "category": "旅行"},
    "🚂": {"name": "火车", "keywords": ["train", "steam"], "category": "旅行"},
    "🚃": {"name": "车厢", "keywords": ["train", "car"], "category": "旅行"},
    "🚄": {"name": "高铁", "keywords": ["bullet train", "fast"], "category": "旅行"},
    "🚅": {"name": "子弹头列车", "keywords": ["bullet train", "shinkansen"], "category": "旅行"},
    "🚆": {"name": "火车", "keywords": ["train"], "category": "旅行"},
    "🚇": {"name": "地铁", "keywords": ["metro", "subway"], "category": "旅行"},
    "🚈": {"name": "轻轨", "keywords": ["light rail"], "category": "旅行"},
    "🚉": {"name": "车站", "keywords": ["station", "train"], "category": "旅行"},
    "🚊": {"name": "电车", "keywords": ["tram", "trolley"], "category": "旅行"},
    "🚝": {"name": "单轨", "keywords": ["monorail"], "category": "旅行"},
    "🚞": {"name": "山区铁路", "keywords": ["mountain", "railway"], "category": "旅行"},
    "🚋": {"name": "有轨电车", "keywords": ["tram", "car"], "category": "旅行"},
    "🚌": {"name": "公交车", "keywords": ["bus"], "category": "旅行"},
    "🚍": {"name": "公交车", "keywords": ["bus", "oncoming"], "category": "旅行"},
    "🚎": {"name": "无轨电车", "keywords": ["trolleybus"], "category": "旅行"},
    "🚐": {"name": "小巴", "keywords": ["minibus", "van"], "category": "旅行"},
    "🚑": {"name": "救护车", "keywords": ["ambulance"], "category": "旅行"},
    "🚒": {"name": "消防车", "keywords": ["fire truck"], "category": "旅行"},
    "🚓": {"name": "警车", "keywords": ["police car"], "category": "旅行"},
    "🚔": {"name": "警车", "keywords": ["police", "oncoming"], "category": "旅行"},
    "🚕": {"name": "出租车", "keywords": ["taxi", "cab"], "category": "旅行"},
    "🚖": {"name": "出租车", "keywords": ["taxi", "oncoming"], "category": "旅行"},
    "🚗": {"name": "汽车", "keywords": ["car", "automobile"], "category": "旅行"},
    "🚘": {"name": "汽车", "keywords": ["car", "oncoming"], "category": "旅行"},
    "🚙": {"name": "SUV", "keywords": ["car", "suv"], "category": "旅行"},
    "🛻": {"name": "皮卡", "keywords": ["pickup truck"], "category": "旅行"},
    "🚚": {"name": "货车", "keywords": ["truck", "delivery"], "category": "旅行"},
    "🚛": {"name": "卡车", "keywords": ["truck", "semi"], "category": "旅行"},
    "🚜": {"name": "拖拉机", "keywords": ["tractor"], "category": "旅行"},
    "🏎️": {"name": "赛车", "keywords": ["race car", "fast"], "category": "旅行"},
    "🏍️": {"name": "摩托车", "keywords": ["motorcycle"], "category": "旅行"},
    "🛵": {"name": "踏板摩托", "keywords": ["scooter"], "category": "旅行"},
    "🚲": {"name": "自行车", "keywords": ["bicycle", "bike"], "category": "旅行"},
    "🛴": {"name": "滑板车", "keywords": ["scooter", "kick"], "category": "旅行"},
    "🛺": {"name": "三轮摩托", "keywords": ["auto rickshaw"], "category": "旅行"},
    "🚔": {"name": "巡逻车", "keywords": ["police car"], "category": "旅行"},
    "🚨": {"name": "警灯", "keywords": ["siren", "alert", "emergency"], "category": "旅行"},
    "🚥": {"name": "交通灯", "keywords": ["traffic light", "horizontal"], "category": "旅行"},
    "🚦": {"name": "交通灯", "keywords": ["traffic light", "vertical"], "category": "旅行"},
    "🚧": {"name": "施工", "keywords": ["construction", "barrier"], "category": "旅行"},
    "⚓": {"name": "锚", "keywords": ["anchor", "ship"], "category": "旅行"},
    "🛟": {"name": "救生圈", "keywords": ["life buoy", "ring"], "category": "旅行"},
    "⛽": {"name": "加油站", "keywords": ["fuel", "gas", "pump"], "category": "旅行"},
    "🚏": {"name": "公交站", "keywords": ["bus stop"], "category": "旅行"},
    "🗺️": {"name": "世界地图", "keywords": ["map", "world"], "category": "旅行"},
    "🗿": {"name": "摩艾", "keywords": ["moai", "easter island"], "category": "旅行"},
    "🗽": {"name": "自由女神", "keywords": ["statue of liberty"], "category": "旅行"},
    "🗼": {"name": "东京塔", "keywords": ["tokyo tower"], "category": "旅行"},
    "🏰": {"name": "城堡", "keywords": ["castle", "european"], "category": "旅行"},
    "🏯": {"name": "日本城堡", "keywords": ["castle", "japanese"], "category": "旅行"},
    "🏟️": {"name": "体育场", "keywords": ["stadium", "arena"], "category": "旅行"},
    "🎡": {"name": "摩天轮", "keywords": ["ferris wheel"], "category": "旅行"},
    "🎢": {"name": "过山车", "keywords": ["roller coaster"], "category": "旅行"},
    "🎠": {"name": "旋转木马", "keywords": ["carousel", "horse"], "category": "旅行"},
    "⛲": {"name": "喷泉", "keywords": ["fountain"], "category": "旅行"},
    "🏖️": {"name": "海滩", "keywords": ["beach", "umbrella"], "category": "旅行"},
    "🏝️": {"name": "荒岛", "keywords": ["island", "desert"], "category": "旅行"},
    "🏜️": {"name": "沙漠", "keywords": ["desert"], "category": "旅行"},
    "🌋": {"name": "火山", "keywords": ["volcano", "eruption"], "category": "旅行"},
    "⛰️": {"name": "山", "keywords": ["mountain"], "category": "旅行"},
    "🏔️": {"name": "雪山", "keywords": ["mountain", "snow"], "category": "旅行"},
    "🗻": {"name": "富士山", "keywords": ["mount fuji"], "category": "旅行"},
    "🏕️": {"name": "露营", "keywords": ["camping", "tent"], "category": "旅行"},
    "🏠": {"name": "房子", "keywords": ["house", "home"], "category": "旅行"},
    "🏡": {"name": "花园房子", "keywords": ["house", "garden"], "category": "旅行"},
    "🏢": {"name": "办公楼", "keywords": ["office", "building"], "category": "旅行"},
    "🏣": {"name": "邮局", "keywords": ["post office", "japanese"], "category": "旅行"},
    "🏤": {"name": "邮局", "keywords": ["post office"], "category": "旅行"},
    "🏥": {"name": "医院", "keywords": ["hospital"], "category": "旅行"},
    "🏦": {"name": "银行", "keywords": ["bank"], "category": "旅行"},
    "🏨": {"name": "酒店", "keywords": ["hotel"], "category": "旅行"},
    "🏩": {"name": "情人酒店", "keywords": ["love hotel"], "category": "旅行"},
    "🏪": {"name": "便利店", "keywords": ["convenience store"], "category": "旅行"},
    "🏬": {"name": "百货商场", "keywords": ["department store"], "category": "旅行"},
    "🏭": {"name": "工厂", "keywords": ["factory"], "category": "旅行"},
    "⛪": {"name": "教堂", "keywords": ["church", "christian"], "category": "旅行"},
    "🕌": {"name": "清真寺", "keywords": ["mosque", "islam"], "category": "旅行"},
    "🕍": {"name": "犹太教堂", "keywords": ["synagogue", "jewish"], "category": "旅行"},
    "🛕": {"name": "印度寺庙", "keywords": ["hindu temple"], "category": "旅行"},
    "⛩️": {"name": "鸟居", "keywords": ["shrine", "japanese"], "category": "旅行"},
    "💻": {"name": "笔记本电脑", "keywords": ["laptop", "computer"], "category": "物品"},
    "🖥️": {"name": "台式电脑", "keywords": ["desktop", "computer", "monitor"], "category": "物品"},
    "🖨️": {"name": "打印机", "keywords": ["printer"], "category": "物品"},
    "⌨️": {"name": "键盘", "keywords": ["keyboard"], "category": "物品"},
    "🖱️": {"name": "鼠标", "keywords": ["mouse", "click"], "category": "物品"},
    "💾": {"name": "软盘", "keywords": ["floppy disk", "save"], "category": "物品"},
    "💿": {"name": "光盘", "keywords": ["cd", "disc"], "category": "物品"},
    "📀": {"name": "DVD", "keywords": ["dvd", "disc"], "category": "物品"},
    "📱": {"name": "手机", "keywords": ["phone", "mobile"], "category": "物品"},
    "📲": {"name": "来电", "keywords": ["phone", "incoming"], "category": "物品"},
    "📞": {"name": "电话", "keywords": ["telephone", "receiver"], "category": "物品"},
    "📟": {"name": "寻呼机", "keywords": ["pager"], "category": "物品"},
    "📠": {"name": "传真机", "keywords": ["fax"], "category": "物品"},
    "🔋": {"name": "电池", "keywords": ["battery"], "category": "物品"},
    "🔌": {"name": "插头", "keywords": ["plug", "electric"], "category": "物品"},
    "💡": {"name": "灯泡", "keywords": ["light", "bulb", "idea"], "category": "物品"},
    "🔦": {"name": "手电筒", "keywords": ["flashlight", "torch"], "category": "物品"},
    "🕯️": {"name": "蜡烛", "keywords": ["candle"], "category": "物品"},
    "🧯": {"name": "灭火器", "keywords": ["fire extinguisher"], "category": "物品"},
    "🛢️": {"name": "油桶", "keywords": ["oil", "drum"], "category": "物品"},
    "💰": {"name": "钱袋", "keywords": ["money", "bag"], "category": "物品"},
    "💴": {"name": "日元", "keywords": ["yen", "money"], "category": "物品"},
    "💵": {"name": "美元", "keywords": ["dollar", "money"], "category": "物品"},
    "💶": {"name": "欧元", "keywords": ["euro", "money"], "category": "物品"},
    "💷": {"name": "英镑", "keywords": ["pound", "money"], "category": "物品"},
    "🪙": {"name": "硬币", "keywords": ["coin", "money"], "category": "物品"},
    "💸": {"name": "飞钱", "keywords": ["money", "wings", "fly"], "category": "物品"},
    "💳": {"name": "信用卡", "keywords": ["credit card", "payment"], "category": "物品"},
    "🧾": {"name": "收据", "keywords": ["receipt", "bill"], "category": "物品"},
    "✉️": {"name": "信封", "keywords": ["envelope", "mail", "letter"], "category": "物品"},
    "📧": {"name": "电子邮件", "keywords": ["email"], "category": "物品"},
    "📨": {"name": "来信", "keywords": ["incoming", "mail"], "category": "物品"},
    "📩": {"name": "发信", "keywords": ["send", "mail"], "category": "物品"},
    "📤": {"name": "发件箱", "keywords": ["outbox", "sent"], "category": "物品"},
    "📥": {"name": "收件箱", "keywords": ["inbox", "receive"], "category": "物品"},
    "📦": {"name": "包裹", "keywords": ["package", "box", "delivery"], "category": "物品"},
    "📫": {"name": "邮箱", "keywords": ["mailbox", "closed"], "category": "物品"},
    "📪": {"name": "邮箱", "keywords": ["mailbox", "empty"], "category": "物品"},
    "📬": {"name": "邮箱", "keywords": ["mailbox", "open"], "category": "物品"},
    "📭": {"name": "邮箱", "keywords": ["mailbox", "no mail"], "category": "物品"},
    "📮": {"name": "邮筒", "keywords": ["postbox", "mail"], "category": "物品"},
    "🗳️": {"name": "投票箱", "keywords": ["ballot box", "vote"], "category": "物品"},
    "✏️": {"name": "铅笔", "keywords": ["pencil", "write"], "category": "物品"},
    "✒️": {"name": "钢笔", "keywords": ["pen", "nib"], "category": "物品"},
    "🖋️": {"name": "钢笔", "keywords": ["pen", "fountain"], "category": "物品"},
    "🖊️": {"name": "圆珠笔", "keywords": ["pen", "ballpoint"], "category": "物品"},
    "🖌️": {"name": "画笔", "keywords": ["paintbrush", "art"], "category": "物品"},
    "🖍️": {"name": "蜡笔", "keywords": ["crayon"], "category": "物品"},
    "📝": {"name": "备忘录", "keywords": ["memo", "note", "write"], "category": "物品"},
    "📁": {"name": "文件夹", "keywords": ["folder", "file"], "category": "物品"},
    "📂": {"name": "打开文件夹", "keywords": ["folder", "open"], "category": "物品"},
    "🗂️": {"name": "分隔页", "keywords": ["tab", "divider"], "category": "物品"},
    "📅": {"name": "日历", "keywords": ["calendar", "date"], "category": "物品"},
    "📆": {"name": "日历", "keywords": ["calendar", "tear-off"], "category": "物品"},
    "🗒️": {"name": "螺旋笔记本", "keywords": ["notepad", "spiral"], "category": "物品"},
    "🗓️": {"name": "日程本", "keywords": ["calendar", "spiral"], "category": "物品"},
    "📇": {"name": "索引卡", "keywords": ["index card", "rolodex"], "category": "物品"},
    "📈": {"name": "上升图表", "keywords": ["chart", "up", "growth"], "category": "物品"},
    "📉": {"name": "下降图表", "keywords": ["chart", "down", "decline"], "category": "物品"},
    "📊": {"name": "柱状图", "keywords": ["bar chart", "statistics"], "category": "物品"},
    "📋": {"name": "剪贴板", "keywords": ["clipboard"], "category": "物品"},
    "📌": {"name": "图钉", "keywords": ["pin", "pushpin"], "category": "物品"},
    "📍": {"name": "大头针", "keywords": ["pin", "location"], "category": "物品"},
    "📎": {"name": "回形针", "keywords": ["paperclip"], "category": "物品"},
    "🖇️": {"name": "回形针", "keywords": ["paperclip", "linked"], "category": "物品"},
    "📏": {"name": "直尺", "keywords": ["ruler", "straight"], "category": "物品"},
    "📐": {"name": "三角尺", "keywords": ["ruler", "triangle"], "category": "物品"},
    "✂️": {"name": "剪刀", "keywords": ["scissors", "cut"], "category": "物品"},
    "🗃️": {"name": "卡片盒", "keywords": ["card file", "box"], "category": "物品"},
    "🗄️": {"name": "文件柜", "keywords": ["file cabinet"], "category": "物品"},
    "🗑️": {"name": "垃圾桶", "keywords": ["trash", "bin", "delete"], "category": "物品"},
    "🔒": {"name": "锁", "keywords": ["lock", "secure"], "category": "物品"},
    "🔓": {"name": "开锁", "keywords": ["unlock", "open"], "category": "物品"},
    "🔏": {"name": "笔锁", "keywords": ["lock", "pen"], "category": "物品"},
    "🔐": {"name": "钥匙锁", "keywords": ["lock", "key"], "category": "物品"},
    "🔑": {"name": "钥匙", "keywords": ["key"], "category": "物品"},
    "🗝️": {"name": "老式钥匙", "keywords": ["key", "old"], "category": "物品"},
    "🔨": {"name": "锤子", "keywords": ["hammer", "tool"], "category": "物品"},
    "🪓": {"name": "斧头", "keywords": ["axe", "chop"], "category": "物品"},
    "⛏️": {"name": "镐", "keywords": ["pickaxe", "mining"], "category": "物品"},
    "⚒️": {"name": "锤子和镐", "keywords": ["hammer", "pick"], "category": "物品"},
    "🛠️": {"name": "工具", "keywords": ["tools", "wrench", "hammer"], "category": "物品"},
    "🗡️": {"name": "匕首", "keywords": ["dagger", "knife"], "category": "物品"},
    "⚔️": {"name": "交叉剑", "keywords": ["swords", "crossed"], "category": "物品"},
    "🔫": {"name": "水枪", "keywords": ["gun", "water", "pistol"], "category": "物品"},
    "🛡️": {"name": "盾牌", "keywords": ["shield", "defense"], "category": "物品"},
    "🔧": {"name": "扳手", "keywords": ["wrench", "tool"], "category": "物品"},
    "🪛": {"name": "螺丝刀", "keywords": ["screwdriver"], "category": "物品"},
    "🔩": {"name": "螺栓", "keywords": ["bolt", "nut", "screw"], "category": "物品"},
    "⚙️": {"name": "齿轮", "keywords": ["gear", "settings", "cog"], "category": "物品"},
    "🗜️": {"name": "夹钳", "keywords": ["clamp", "compress"], "category": "物品"},
    "⚖️": {"name": "天平", "keywords": ["balance", "scale", "justice"], "category": "物品"},
    "🔗": {"name": "链接", "keywords": ["link", "chain"], "category": "物品"},
    "⛓️": {"name": "链条", "keywords": ["chains", "link"], "category": "物品"},
    "🧰": {"name": "工具箱", "keywords": ["toolbox"], "category": "物品"},
    "🧲": {"name": "磁铁", "keywords": ["magnet", "attract"], "category": "物品"},
    "💎": {"name": "钻石", "keywords": ["diamond", "gem"], "category": "物品"},
    "🔮": {"name": "水晶球", "keywords": ["crystal ball", "fortune"], "category": "物品"},
    "🧿": {"name": "恶魔之眼", "keywords": ["nazar", "evil eye"], "category": "物品"},
    "🪬": {"name": "法蒂玛之手", "keywords": ["hamsa", "amulet"], "category": "物品"},
    "🔭": {"name": "望远镜", "keywords": ["telescope", "space"], "category": "物品"},
    "🔬": {"name": "显微镜", "keywords": ["microscope", "science"], "category": "物品"},
    "🕳️": {"name": "洞", "keywords": ["hole", "void"], "category": "物品"},
    "🩹": {"name": "创可贴", "keywords": ["bandage", "band-aid"], "category": "物品"},
    "🩺": {"name": "听诊器", "keywords": ["stethoscope", "doctor"], "category": "物品"},
    "💊": {"name": "药丸", "keywords": ["pill", "medicine"], "category": "物品"},
    "💉": {"name": "注射器", "keywords": ["syringe", "vaccine"], "category": "物品"},
    "🧬": {"name": "DNA", "keywords": ["dna", "genetics"], "category": "物品"},
    "🧫": {"name": "培养皿", "keywords": ["petri dish", "biology"], "category": "物品"},
    "🧪": {"name": "试管", "keywords": ["test tube", "chemistry"], "category": "物品"},
    "🌡️": {"name": "温度计", "keywords": ["thermometer", "temperature"], "category": "物品"},
    "🧹": {"name": "扫帚", "keywords": ["broom", "sweep"], "category": "物品"},
    "🧺": {"name": "篮子", "keywords": ["basket", "laundry"], "category": "物品"},
    "🧻": {"name": "卫生纸", "keywords": ["toilet paper", "roll"], "category": "物品"},
    "🚽": {"name": "马桶", "keywords": ["toilet"], "category": "物品"},
    "🚿": {"name": "淋浴", "keywords": ["shower"], "category": "物品"},
    "🛁": {"name": "浴缸", "keywords": ["bathtub", "bath"], "category": "物品"},
    "🧴": {"name": "乳液瓶", "keywords": ["lotion", "bottle"], "category": "物品"},
    "🧷": {"name": "安全别针", "keywords": ["safety pin"], "category": "物品"},
    "🧼": {"name": "肥皂", "keywords": ["soap", "wash"], "category": "物品"},
    "🫧": {"name": "泡泡", "keywords": ["bubbles", "soap"], "category": "物品"},
    "🪥": {"name": "牙刷", "keywords": ["toothbrush"], "category": "物品"},
    "🧽": {"name": "海绵", "keywords": ["sponge", "absorb"], "category": "物品"},
    "🪣": {"name": "桶", "keywords": ["bucket", "pail"], "category": "物品"},
    "🔑": {"name": "钥匙", "keywords": ["key"], "category": "物品"},
    "🗝️": {"name": "古钥匙", "keywords": ["key", "old", "vintage"], "category": "物品"},
    "🚪": {"name": "门", "keywords": ["door"], "category": "物品"},
    "🛋️": {"name": "沙发", "keywords": ["sofa", "couch"], "category": "物品"},
    "🪑": {"name": "椅子", "keywords": ["chair", "seat"], "category": "物品"},
    "🛏️": {"name": "床", "keywords": ["bed", "sleep"], "category": "物品"},
    "🪞": {"name": "镜子", "keywords": ["mirror", "reflection"], "category": "物品"},
    "🪟": {"name": "窗户", "keywords": ["window"], "category": "物品"},
    "🛒": {"name": "购物车", "keywords": ["shopping cart", "buy"], "category": "物品"},
    "🎁": {"name": "礼物", "keywords": ["gift", "present", "birthday"], "category": "物品"},
    "🎈": {"name": "气球", "keywords": ["balloon", "party"], "category": "物品"},
    "🎀": {"name": "丝带", "keywords": ["ribbon", "bow"], "category": "物品"},
    "🎊": {"name": "彩球", "keywords": ["confetti ball"], "category": "物品"},
    "🎉": {"name": "拉炮", "keywords": ["party popper", "celebrate"], "category": "物品"},
    "🎎": {"name": "人偶", "keywords": ["dolls", "japanese"], "category": "物品"},
    "🏮": {"name": "灯笼", "keywords": ["lantern", "red"], "category": "物品"},
    "🎐": {"name": "风铃", "keywords": ["wind chime"], "category": "物品"},
    "🧧": {"name": "红包", "keywords": ["red envelope", "money"], "category": "物品"},
    "🎀": {"name": "蝴蝶结", "keywords": ["ribbon", "bow"], "category": "物品"},
    "🔮": {"name": "魔法球", "keywords": ["crystal ball", "magic"], "category": "物品"},
    "🧿": {"name": "护身符", "keywords": ["amulet", "nazar"], "category": "物品"},
    "🪬": {"name": "幸运手", "keywords": ["hamsa", "luck"], "category": "物品"},
    "👕": {"name": "T恤", "keywords": ["tshirt", "shirt", "clothes"], "category": "物品"},
    "👖": {"name": "牛仔裤", "keywords": ["jeans", "pants"], "category": "物品"},
    "🧣": {"name": "围巾", "keywords": ["scarf", "winter"], "category": "物品"},
    "🧤": {"name": "手套", "keywords": ["gloves", "winter"], "category": "物品"},
    "🧥": {"name": "外套", "keywords": ["coat", "jacket"], "category": "物品"},
    "🧦": {"name": "袜子", "keywords": ["socks"], "category": "物品"},
    "👗": {"name": "连衣裙", "keywords": ["dress", "clothes"], "category": "物品"},
    "👘": {"name": "和服", "keywords": ["kimono", "japanese"], "category": "物品"},
    "🥻": {"name": "纱丽", "keywords": ["sari", "indian"], "category": "物品"},
    "🩱": {"name": "泳衣", "keywords": ["swimsuit", "one piece"], "category": "物品"},
    "🩲": {"name": "内裤", "keywords": ["briefs", "underwear"], "category": "物品"},
    "🩳": {"name": "短裤", "keywords": ["shorts"], "category": "物品"},
    "👙": {"name": "比基尼", "keywords": ["bikini", "swimsuit"], "category": "物品"},
    "👚": {"name": "女式衬衫", "keywords": ["blouse", "clothes"], "category": "物品"},
    "👛": {"name": "钱包", "keywords": ["purse", "wallet"], "category": "物品"},
    "👜": {"name": "手提包", "keywords": ["handbag", "bag"], "category": "物品"},
    "👝": {"name": "小包", "keywords": ["pouch", "clutch"], "category": "物品"},
    "🎒": {"name": "背包", "keywords": ["backpack", "school"], "category": "物品"},
    "🩴": {"name": "拖鞋", "keywords": ["flip flop", "sandal"], "category": "物品"},
    "👞": {"name": "皮鞋", "keywords": ["shoe", "dress"], "category": "物品"},
    "👟": {"name": "运动鞋", "keywords": ["sneaker", "running"], "category": "物品"},
    "🥾": {"name": "登山靴", "keywords": ["boot", "hiking"], "category": "物品"},
    "🥿": {"name": "平底鞋", "keywords": ["flat shoe", "ballet"], "category": "物品"},
    "👠": {"name": "高跟鞋", "keywords": ["high heel", "shoe"], "category": "物品"},
    "👡": {"name": "凉鞋", "keywords": ["sandal", "shoe"], "category": "物品"},
    "👢": {"name": "靴子", "keywords": ["boot"], "category": "物品"},
    "👑": {"name": "皇冠", "keywords": ["crown", "king", "queen"], "category": "物品"},
    "👒": {"name": "帽子", "keywords": ["hat", "woman"], "category": "物品"},
    "🎩": {"name": "礼帽", "keywords": ["top hat", "magic"], "category": "物品"},
    "🎓": {"name": "学位帽", "keywords": ["graduation", "cap"], "category": "物品"},
    "🧢": {"name": "鸭舌帽", "keywords": ["cap", "baseball"], "category": "物品"},
    "🪖": {"name": "军盔", "keywords": ["helmet", "military"], "category": "物品"},
    "⛑️": {"name": "救援头盔", "keywords": ["helmet", "rescue"], "category": "物品"},
    "📿": {"name": "念珠", "keywords": ["prayer beads", "rosary"], "category": "物品"},
    "💄": {"name": "口红", "keywords": ["lipstick", "makeup"], "category": "物品"},
    "💍": {"name": "戒指", "keywords": ["ring", "diamond"], "category": "物品"},
    "💎": {"name": "宝石", "keywords": ["gem", "diamond", "jewel"], "category": "物品"},
    "🔇": {"name": "静音", "keywords": ["mute", "quiet", "silent"], "category": "符号"},
    "🔈": {"name": "低音量", "keywords": ["volume", "low"], "category": "符号"},
    "🔉": {"name": "中音量", "keywords": ["volume", "medium"], "category": "符号"},
    "🔊": {"name": "高音量", "keywords": ["volume", "high", "loud"], "category": "符号"},
    "📢": {"name": "扩音器", "keywords": ["megaphone", "announce"], "category": "符号"},
    "📣": {"name": "喇叭", "keywords": ["megaphone", "cheer"], "category": "符号"},
    "🔔": {"name": "铃铛", "keywords": ["bell", "ring"], "category": "符号"},
    "🔕": {"name": "静音铃", "keywords": ["bell", "mute", "no"], "category": "符号"},
    "🎵": {"name": "音符", "keywords": ["music", "note"], "category": "符号"},
    "🎶": {"name": "双音符", "keywords": ["music", "notes"], "category": "符号"},
    "⚠️": {"name": "警告", "keywords": ["warning", "caution"], "category": "符号"},
    "🚫": {"name": "禁止", "keywords": ["no", "prohibited", "stop"], "category": "符号"},
    "🔞": {"name": "18禁", "keywords": ["18", "underage", "nsfw"], "category": "符号"},
    "📵": {"name": "禁止手机", "keywords": ["no phone", "mobile"], "category": "符号"},
    "🚭": {"name": "禁止吸烟", "keywords": ["no smoking"], "category": "符号"},
    "❗": {"name": "感叹号", "keywords": ["exclamation", "warning"], "category": "符号"},
    "❕": {"name": "白色感叹号", "keywords": ["exclamation", "white"], "category": "符号"},
    "❓": {"name": "问号", "keywords": ["question", "what"], "category": "符号"},
    "❔": {"name": "白色问号", "keywords": ["question", "white"], "category": "符号"},
    "‼️": {"name": "双感叹号", "keywords": ["exclamation", "double"], "category": "符号"},
    "⁉️": {"name": "感叹问号", "keywords": ["exclamation", "question"], "category": "符号"},
    "⭕": {"name": "圆圈", "keywords": ["circle", "ring", "correct"], "category": "符号"},
    "✅": {"name": "绿色勾选", "keywords": ["check", "yes", "done"], "category": "符号"},
    "☑️": {"name": "勾选框", "keywords": ["check", "box", "vote"], "category": "符号"},
    "✔️": {"name": "勾选", "keywords": ["check", "mark", "yes"], "category": "符号"},
    "❌": {"name": "叉", "keywords": ["cross", "no", "wrong"], "category": "符号"},
    "❎": {"name": "叉号按钮", "keywords": ["cross", "mark", "button"], "category": "符号"},
    "➕": {"name": "加号", "keywords": ["plus", "add"], "category": "符号"},
    "➖": {"name": "减号", "keywords": ["minus", "subtract"], "category": "符号"},
    "➗": {"name": "除号", "keywords": ["divide", "division"], "category": "符号"},
    "✖️": {"name": "乘号", "keywords": ["multiply", "times"], "category": "符号"},
    "♾️": {"name": "无限", "keywords": ["infinity", "forever"], "category": "符号"},
    "💯": {"name": "满分", "keywords": ["100", "perfect", "score"], "category": "符号"},
    "🔴": {"name": "红圈", "keywords": ["red", "circle"], "category": "符号"},
    "🟠": {"name": "橙圈", "keywords": ["orange", "circle"], "category": "符号"},
    "🟡": {"name": "黄圈", "keywords": ["yellow", "circle"], "category": "符号"},
    "🟢": {"name": "绿圈", "keywords": ["green", "circle"], "category": "符号"},
    "🔵": {"name": "蓝圈", "keywords": ["blue", "circle"], "category": "符号"},
    "🟣": {"name": "紫圈", "keywords": ["purple", "circle"], "category": "符号"},
    "🟤": {"name": "棕圈", "keywords": ["brown", "circle"], "category": "符号"},
    "⚫": {"name": "黑圈", "keywords": ["black", "circle"], "category": "符号"},
    "⚪": {"name": "白圈", "keywords": ["white", "circle"], "category": "符号"},
    "🔺": {"name": "红色三角", "keywords": ["red", "triangle", "up"], "category": "符号"},
    "🔻": {"name": "红色倒三角", "keywords": ["red", "triangle", "down"], "category": "符号"},
    "🔸": {"name": "橙色菱形", "keywords": ["orange", "diamond"], "category": "符号"},
    "🔹": {"name": "蓝色菱形", "keywords": ["blue", "diamond"], "category": "符号"},
    "🔶": {"name": "大橙色菱形", "keywords": ["orange", "diamond", "large"], "category": "符号"},
    "🔷": {"name": "大蓝色菱形", "keywords": ["blue", "diamond", "large"], "category": "符号"},
    "▪️": {"name": "黑色方块", "keywords": ["black", "square", "small"], "category": "符号"},
    "▫️": {"name": "白色方块", "keywords": ["white", "square", "small"], "category": "符号"},
    "◾": {"name": "中小黑方块", "keywords": ["black", "square", "medium"], "category": "符号"},
    "◽": {"name": "中小白方块", "keywords": ["white", "square", "medium"], "category": "符号"},
    "◻️": {"name": "中白方块", "keywords": ["white", "square", "medium"], "category": "符号"},
    "◼️": {"name": "中黑方块", "keywords": ["black", "square", "medium"], "category": "符号"},
    "🟥": {"name": "红色方块", "keywords": ["red", "square"], "category": "符号"},
    "🟧": {"name": "橙色方块", "keywords": ["orange", "square"], "category": "符号"},
    "🟨": {"name": "黄色方块", "keywords": ["yellow", "square"], "category": "符号"},
    "🟩": {"name": "绿色方块", "keywords": ["green", "square"], "category": "符号"},
    "🟦": {"name": "蓝色方块", "keywords": ["blue", "square"], "category": "符号"},
    "🟪": {"name": "紫色方块", "keywords": ["purple", "square"], "category": "符号"},
    "🟫": {"name": "棕色方块", "keywords": ["brown", "square"], "category": "符号"},
    "🏳️": {"name": "白旗", "keywords": ["white flag", "surrender"], "category": "旗帜"},
    "🏴": {"name": "黑旗", "keywords": ["black flag"], "category": "旗帜"},
    "🏁": {"name": "方格旗", "keywords": ["checkered flag", "race"], "category": "旗帜"},
    "🚩": {"name": "三角旗", "keywords": ["triangular flag", "red"], "category": "旗帜"},
    "🏳️‍🌈": {"name": "彩虹旗", "keywords": ["rainbow flag", "pride"], "category": "旗帜"},
    "🏳️‍⚧️": {"name": "跨性别旗", "keywords": ["transgender flag"], "category": "旗帜"},
    "🇨🇳": {"name": "中国", "keywords": ["china", "flag", "cn"], "category": "旗帜"},
    "🇺🇸": {"name": "美国", "keywords": ["usa", "flag", "us"], "category": "旗帜"},
    "🇯🇵": {"name": "日本", "keywords": ["japan", "flag", "jp"], "category": "旗帜"},
    "🇰🇷": {"name": "韩国", "keywords": ["korea", "flag", "kr"], "category": "旗帜"},
    "🇬🇧": {"name": "英国", "keywords": ["uk", "britain", "gb"], "category": "旗帜"},
    "🇫🇷": {"name": "法国", "keywords": ["france", "flag", "fr"], "category": "旗帜"},
    "🇩🇪": {"name": "德国", "keywords": ["germany", "flag", "de"], "category": "旗帜"},
    "🇮🇹": {"name": "意大利", "keywords": ["italy", "flag", "it"], "category": "旗帜"},
    "🇪🇸": {"name": "西班牙", "keywords": ["spain", "flag", "es"], "category": "旗帜"},
    "🇷🇺": {"name": "俄罗斯", "keywords": ["russia", "flag", "ru"], "category": "旗帜"},
    "🇧🇷": {"name": "巴西", "keywords": ["brazil", "flag", "br"], "category": "旗帜"},
    "🇦🇺": {"name": "澳大利亚", "keywords": ["australia", "flag", "au"], "category": "旗帜"},
    "🇨🇦": {"name": "加拿大", "keywords": ["canada", "flag", "ca"], "category": "旗帜"},
    "🇮🇳": {"name": "印度", "keywords": ["india", "flag", "in"], "category": "旗帜"},
    "🇹🇭": {"name": "泰国", "keywords": ["thailand", "flag", "th"], "category": "旗帜"},
    "🇻🇳": {"name": "越南", "keywords": ["vietnam", "flag", "vn"], "category": "旗帜"},
    "🇸🇬": {"name": "新加坡", "keywords": ["singapore", "flag", "sg"], "category": "旗帜"},
    "🇲🇾": {"name": "马来西亚", "keywords": ["malaysia", "flag", "my"], "category": "旗帜"},
    "🇮🇩": {"name": "印度尼西亚", "keywords": ["indonesia", "flag", "id"], "category": "旗帜"},
    "🇵🇭": {"name": "菲律宾", "keywords": ["philippines", "flag", "ph"], "category": "旗帜"},
    "🇹🇷": {"name": "土耳其", "keywords": ["turkey", "flag", "tr"], "category": "旗帜"},
    "🇸🇦": {"name": "沙特阿拉伯", "keywords": ["saudi", "flag", "sa"], "category": "旗帜"},
    "🇦🇪": {"name": "阿联酋", "keywords": ["uae", "emirates", "ae"], "category": "旗帜"},
    "🇮🇱": {"name": "以色列", "keywords": ["israel", "flag", "il"], "category": "旗帜"},
    "🇪🇬": {"name": "埃及", "keywords": ["egypt", "flag", "eg"], "category": "旗帜"},
    "🇿🇦": {"name": "南非", "keywords": ["south africa", "flag", "za"], "category": "旗帜"},
    "🇳🇬": {"name": "尼日利亚", "keywords": ["nigeria", "flag", "ng"], "category": "旗帜"},
    "🇰🇪": {"name": "肯尼亚", "keywords": ["kenya", "flag", "ke"], "category": "旗帜"},
    "🇲🇽": {"name": "墨西哥", "keywords": ["mexico", "flag", "mx"], "category": "旗帜"},
    "🇦🇷": {"name": "阿根廷", "keywords": ["argentina", "flag", "ar"], "category": "旗帜"},
    "🇨🇱": {"name": "智利", "keywords": ["chile", "flag", "cl"], "category": "旗帜"},
    "🇨🇴": {"name": "哥伦比亚", "keywords": ["colombia", "flag", "co"], "category": "旗帜"},
    "🇵🇪": {"name": "秘鲁", "keywords": ["peru", "flag", "pe"], "category": "旗帜"},
    "🇳🇿": {"name": "新西兰", "keywords": ["new zealand", "flag", "nz"], "category": "旗帜"},
    "🇭🇰": {"name": "香港", "keywords": ["hong kong", "flag", "hk"], "category": "旗帜"},
    "🇹🇼": {"name": "台湾", "keywords": ["taiwan", "flag", "tw"], "category": "旗帜"},
    "🇲🇴": {"name": "澳门", "keywords": ["macau", "flag", "mo"], "category": "旗帜"},
}

CATEGORIES = [
    ("⭐", "全部"),
    ("🕐", "最近使用"),
    ("❤️", "收藏"),
    ("😀", "表情"),
    ("👋", "手势"),
    ("🐶", "动物"),
    ("🍔", "食物"),
    ("⚽", "活动"),
    ("✈️", "旅行"),
    ("💡", "物品"),
    ("♻️", "符号"),
    ("🏁", "旗帜"),
]

SKIN_TONES = [
    ("", "默认"),
    ("\U0001F3FB", "🏻 浅肤色"),
    ("\U0001F3FC", "🏼 中浅"),
    ("\U0001F3FD", "🏽 中等"),
    ("\U0001F3FE", "🏾 中深"),
    ("\U0001F3FF", "🏿 深肤色"),
]

DATA_DIR = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "EmojiPicker"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return default


def _save_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Emoji button widget
# ---------------------------------------------------------------------------

class EmojiButton(QPushButton):
    """A single emoji tile in the grid."""
    double_clicked = pyqtSignal(str)

    def __init__(self, emoji_char: str, parent=None):
        super().__init__(emoji_char, parent)
        self.emoji_char = emoji_char
        self.setFixedSize(48, 48)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setToolTip(emoji_char)
        self.setStyleSheet("""
            QPushButton {
                background-color: #111122;
                border: 1px solid #222244;
                border-radius: 10px;
                font-size: 26px;
                padding: 0;
            }
            QPushButton:hover {
                background-color: #1a1a3a;
                border: 1px solid #667eea;
            }
            QPushButton:pressed {
                background-color: #222255;
            }
        """)

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit(self.emoji_char)
        super().mouseDoubleClickEvent(event)


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class EmojiPicker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎨 Emoji 选择器")
        self.setMinimumSize(640, 520)
        self.resize(700, 580)

        self.favorites = _load_json(DATA_DIR / "favorites.json", [])
        self.recent = _load_json(DATA_DIR / "recent.json", [])
        self.current_skin = ""

        self._build_ui()
        self._apply_theme()
        self._build_tray()
        self._load_category("全部")

    # ---- UI ----

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("🎨 Emoji 选择器")
        title.setFont(QFont("Segoe UI Emoji", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff;")
        hdr.addWidget(title)
        hdr.addStretch()

        self.skin_combo = QComboBox()
        for _, label in SKIN_TONES:
            self.skin_combo.addItem(label)
        self.skin_combo.setFixedWidth(110)
        self.skin_combo.setStyleSheet("""
            QComboBox {
                background: #111122; color: #ccc; border:1px solid #333;
                border-radius:6px; padding:4px 8px;
            }
            QComboBox QAbstractItemView {
                background:#111122; color:#ccc; selection-background-color:#333366;
            }
        """)
        self.skin_combo.currentIndexChanged.connect(self._on_skin_change)
        hdr.addWidget(self.skin_combo)

        minimize_btn = QPushButton("—")
        minimize_btn.setFixedSize(32, 32)
        minimize_btn.setToolTip("最小化到托盘")
        minimize_btn.clicked.connect(self.hide)
        minimize_btn.setStyleSheet("""
            QPushButton { background:#222; color:#888; border:none; border-radius:6px; font-size:14px; }
            QPushButton:hover { background:#333; color:#fff; }
        """)
        hdr.addWidget(minimize_btn)
        root.addLayout(hdr)

        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索 emoji (名称、关键词)...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._on_search)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: #111122; color: #eee; border: 1px solid #333;
                border-radius: 8px; padding: 8px 14px; font-size: 14px;
            }
            QLineEdit:focus { border: 1px solid #667eea; }
        """)
        root.addWidget(self.search_input)

        # Category tabs
        self.cat_tabs = QTabWidget()
        self.cat_tabs.setStyleSheet("""
            QTabWidget::pane { border: none; }
            QTabBar::tab {
                background: #111122; color: #999; padding: 6px 10px;
                margin-right: 2px; border-radius: 6px 6px 0 0; font-size: 13px;
            }
            QTabBar::tab:selected { background: #1a1a3a; color: #fff; border-bottom: 2px solid #667eea; }
            QTabBar::tab:hover { background: #1a1a3a; color: #ccc; }
        """)
        for icon, label in CATEGORIES:
            page = QWidget()
            self.cat_tabs.addTab(page, f"{icon} {label}")
        self.cat_tabs.currentChanged.connect(self._on_cat_changed)
        root.addWidget(self.cat_tabs)

        # Info bar
        self.info_label = QLabel("双击 emoji 即可复制到剪贴板")
        self.info_label.setStyleSheet("color: #667eea; font-size: 12px; padding: 2px 4px;")
        root.addWidget(self.info_label)

        # Emoji grid inside each tab
        self._grids: dict[int, QWidget] = {}
        self._grid_layouts: dict[int, QGridLayout] = {}
        self._scroll_areas: dict[int, QScrollArea] = {}
        for idx in range(self.cat_tabs.count()):
            page = self.cat_tabs.widget(idx)
            lay = QVBoxLayout(page)
            lay.setContentsMargins(0, 0, 0, 0)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }"
                                 "QScrollBar:vertical { background: #0a0a0a; width: 8px; }"
                                 "QScrollBar::handle:vertical { background: #333; border-radius: 4px; }")
            inner = QWidget()
            inner.setStyleSheet("background: transparent;")
            grid = QGridLayout(inner)
            grid.setSpacing(4)
            grid.setContentsMargins(6, 6, 6, 6)
            scroll.setWidget(inner)
            lay.addWidget(scroll)
            self._scroll_areas[idx] = scroll
            self._grid_layouts[idx] = grid

    # ---- Theme ----

    def _apply_theme(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #0a0a0a; }
            QWidget { background-color: #0a0a0a; color: #ddd; }
            QToolTip {
                background: #1a1a3a; color: #fff; border: 1px solid #667eea;
                padding: 6px; border-radius: 6px; font-size: 13px;
            }
        """)

    # ---- Tray ----

    def _build_tray(self):
        # Create a simple colored icon programmatically
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(0, 0, 0, 0))
        p = QPainter(pixmap)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        gradient = QLinearGradient(0, 0, 64, 64)
        gradient.setColorAt(0, QColor("#667eea"))
        gradient.setColorAt(1, QColor("#764ba2"))
        p.setBrush(gradient)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, 64, 64, 14, 14)
        p.setFont(QFont("Segoe UI Emoji", 28))
        p.setPen(QColor("white"))
        p.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "😀")
        p.end()

        self.tray = QSystemTrayIcon(QIcon(pixmap), self)
        menu = QMenu()
        menu.setStyleSheet("QMenu { background: #111122; color: #ccc; }"
                           "QMenu::item:selected { background: #333366; }")
        show_act = menu.addAction("显示窗口")
        show_act.triggered.connect(self._show_from_tray)
        quit_act = menu.addAction("退出")
        quit_act.triggered.connect(self._quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.setToolTip("Emoji 选择器 — 双击打开")
        self.tray.show()

    def _show_from_tray(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_from_tray()

    def _quit(self):
        self.tray.hide()
        QApplication.quit()

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    # ---- Category change ----

    def _on_cat_changed(self, idx: int):
        self.search_input.clear()
        cat_label = CATEGORIES[idx][1]
        self._load_category(cat_label)

    # ---- Search ----

    def _on_search(self, text: str):
        text = text.strip().lower()
        if not text:
            cat_label = CATEGORIES[self.cat_tabs.currentIndex()][1]
            self._load_category(cat_label)
            return
        results = [e for e, d in EMOJI_DATA.items()
                   if text in d["name"].lower() or any(text in kw for kw in d["keywords"])]
        self._populate_grid(self.cat_tabs.currentIndex(), results)

    # ---- Populate grid ----

    def _load_category(self, label: str):
        idx = self.cat_tabs.currentIndex()
        if label == "全部":
            emojis = list(EMOJI_DATA.keys())
        elif label == "最近使用":
            emojis = list(self.recent)
        elif label == "收藏":
            emojis = list(self.favorites)
        else:
            emojis = [e for e, d in EMOJI_DATA.items() if d.get("category") == label]
        self._populate_grid(idx, emojis)

    def _populate_grid(self, tab_idx: int, emojis: list[str]):
        grid = self._grid_layouts[tab_idx]
        # Clear
        while grid.count():
            item = grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        cols = max(1, (self.width() - 40) // 52)
        for i, emoji_char in enumerate(emojis):
            btn = EmojiButton(emoji_char)
            btn.clicked.connect(lambda _, e=emoji_char: self._copy_emoji(e))
            btn.double_clicked.connect(lambda e=emoji_char: self._copy_emoji(e))
            btn.setToolTip(self._tooltip_for(emoji_char))
            btn.enterEvent = lambda ev, e=emoji_char, b=btn: self._show_info(e)
            grid.addWidget(btn, i // cols, i % cols)

        if not emojis:
            empty = QLabel("暂无数据")
            empty.setStyleSheet("color: #555; font-size: 14px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(empty, 0, 0, 1, cols)

    def _tooltip_for(self, emoji_char: str) -> str:
        info = EMOJI_DATA.get(emoji_char, {})
        cp = "U+" + " U+".join(f"{ord(c):04X}" for c in emoji_char)
        return f"{info.get('name', emoji_char)}\n{info.get('category', '')}\n{cp}"

    def _show_info(self, emoji_char: str):
        info = EMOJI_DATA.get(emoji_char, {})
        cp = "U+" + " U+".join(f"{ord(c):04X}" for c in emoji_char)
        fav = "❤️ 已收藏" if emoji_char in self.favorites else ""
        self.info_label.setText(
            f"{emoji_char}  {info.get('name', '')}  |  {info.get('category', '')}  |  {cp}  {fav}"
        )

    # ---- Copy ----

    def _copy_emoji(self, emoji_char: str):
        if self.current_skin and len(emoji_char) == 1 and ord(emoji_char) in self._skin_compatible():
            emoji_char = emoji_char + self.current_skin
        clipboard = QApplication.clipboard()
        clipboard.setText(emoji_char)
        self.tray.showMessage("已复制!", f"{emoji_char} 已复制到剪贴板",
                              QSystemTrayIcon.MessageIcon.Information, 1500)
        # Update recent
        if emoji_char in self.recent:
            self.recent.remove(emoji_char)
        self.recent.insert(0, emoji_char)
        self.recent = self.recent[:50]
        _save_json(DATA_DIR / "recent.json", self.recent)
        self._load_category(CATEGORIES[self.cat_tabs.currentIndex()][1])

    @staticmethod
    def _skin_compatible() -> set[int]:
        """Codepoints that support skin-tone modifiers (simplified set)."""
        return set(range(0x1F44B, 0x1F450)) | {0x1F446, 0x1F447, 0x1F448, 0x1F449,
                                                 0x261D, 0x270A, 0x270B, 0x270C, 0x270D,
                                                 0x1F44A, 0x1F44B, 0x1F44C, 0x1F44D, 0x1F44E,
                                                 0x1F44F, 0x1F450, 0x1F645, 0x1F646, 0x1F647,
                                                 0x1F64B, 0x1F64C, 0x1F64D, 0x1F64E, 0x1F64F,
                                                 0x1F918, 0x1F919, 0x1F91A, 0x1F91B, 0x1F91C,
                                                 0x1F91D, 0x1F91E, 0x1F91F, 0x1F926, 0x1F930,
                                                 0x1F931, 0x1F932, 0x1F933, 0x1F934, 0x1F935,
                                                 0x1F936, 0x1F937, 0x1F938, 0x1F939, 0x1F93D,
                                                 0x1F93E, 0x1F977, 0x1FAF0, 0x1FAF1, 0x1FAF2,
                                                 0x1FAF3, 0x1FAF4, 0x1FAF5, 0x1FAF6, 0x1FAF7,
                                                 0x1FAF8}

    # ---- Skin tone ----

    def _on_skin_change(self, idx: int):
        self.current_skin = SKIN_TONES[idx][0]

    # ---- Favorites (right-click) ----

    def contextMenuEvent(self, event):
        child = self.childAt(event.pos())
        if isinstance(child, EmojiButton):
            menu = QMenu(self)
            menu.setStyleSheet("QMenu { background:#111122; color:#ccc; } QMenu::item:selected { background:#333366; }")
            emoji_char = child.emoji_char
            if emoji_char in self.favorites:
                act = menu.addAction("💔 取消收藏")
            else:
                act = act = menu.addAction("❤️ 添加收藏")
            act.triggered.connect(lambda: self._toggle_favorite(emoji_char))
            menu.exec(event.globalPos())

    def _toggle_favorite(self, emoji_char: str):
        if emoji_char in self.favorites:
            self.favorites.remove(emoji_char)
        else:
            self.favorites.append(emoji_char)
        _save_json(DATA_DIR / "favorites.json", self.favorites)
        self._load_category(CATEGORIES[self.cat_tabs.currentIndex()][1])

    # ---- Resize -> reflow grid ----

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(50, lambda: self._load_category(CATEGORIES[self.cat_tabs.currentIndex()][1]))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    picker = EmojiPicker()
    picker.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
