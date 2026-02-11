"""
Panda Character - Always-present animated panda companion
Manages panda moods, animations, interactions, and easter eggs
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import random
from typing import List, Optional, Dict, Set
from enum import Enum
import threading
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class PandaGender(Enum):
    """Panda gender options."""
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"


class PandaMood(Enum):
    """Panda mood states."""
    HAPPY = "happy"
    EXCITED = "excited"
    WORKING = "working"
    TIRED = "tired"
    CELEBRATING = "celebrating"
    SLEEPING = "sleeping"
    SARCASTIC = "sarcastic"
    RAGE = "rage"
    DRUNK = "drunk"
    EXISTENTIAL = "existential"
    MOTIVATING = "motivating"
    TECH_SUPPORT = "tech_support"
    SLEEPY = "sleepy"


class PandaCharacter:
    """Manages the panda companion character - always present.
    
    The panda is rendered as a canvas-drawn character in panda_widget.py.
    Animation states listed here are used by the canvas drawing system to
    determine body motion, eye styles, mouth styles, and visual extras.
    """
    
    # Configuration constants
    RAGE_CLICK_THRESHOLD = 10  # Number of clicks to trigger rage mode
    
    # Body part region boundaries (relative Y position 0.0-1.0)
    # Adjusted to match actual canvas drawing proportions
    HEAD_BOUNDARY = 0.32
    BODY_BOUNDARY = 0.55
    BUTT_BOUNDARY = 0.75
    
    # Valid animation state names used by the canvas-drawn panda
    ANIMATION_STATES = [
        'idle', 'working', 'celebrating', 'rage', 'sarcastic', 'drunk',
        'playing', 'eating', 'customizing', 'sleeping', 'laying_down',
        'laying_back', 'laying_side', 'dancing', 'petting', 'gaming',
        'thinking', 'dragging', 'wall_hit', 'tossed', 'clicked', 'fed',
        'stretching', 'waving', 'jumping', 'yawning', 'sneezing', 'tail_wag',
        'cartwheel', 'backflip', 'spinning', 'shaking', 'rolling',
        'carrying', 'sitting', 'belly_grab', 'lay_on_back', 'lay_on_side',
        'belly_jiggle',
    ]
    
    # Panda click responses
    CLICK_RESPONSES = [
        "🐼 Hi there!",
        "🐼 Need something?",
        "🐼 *happy panda noises*",
        "🐼 Ready to work!",
        "🐼 At your service!",
        "🐼 Panda reporting for duty!",
        "🐼 What's up?",
        "🐼 How can I help?",
        "🐼 *munches bamboo*",
        "🐼 Still here, still awesome!",
        "🐼 Hey! Watch the fur!",
        "🐼 *boop* Right back at ya!",
        "🐼 Did you bring bamboo?",
        "🐼 I was napping... 😴",
        "🐼 Click me again, I dare you!",
        "🐼 *waves paw* Hiya!",
        "🐼 You rang? 🔔",
        "🐼 Panda at your service! What's the mission?",
        "🐼 *yawns* I'm awake, I'm awake!",
        "🐼 Oh! You startled me! 😲",
        "🐼 Just doing panda things, you know... 🎋",
        "🐼 Did someone say snacks?",
        "🐼 *stretches* Ah, that feels good!",
        "🐼 Another click? You're persistent!",
        "🐼 I'm here for moral support! 💪",
        "🐼 Texture sorting is my passion! 🖼️",
        "🐼 *does a little dance* 💃",
        "🐼 You're doing great, keep it up!",
        "🐼 Panda power activated! ⚡",
        "🐼 Yes, yes, I see you there!",
        "🐼 Want to hear a bamboo joke? ...Nah, they're too corny.",
        "🐼 I'm basically a professional click receiver now.",
        "🐼 *adjusts imaginary glasses* Professional panda, reporting!",
        "🐼 Living my best panda life! ✨",
        "🐼 Did you know pandas can climb trees? Cool, right?",
        "🐼 *does a backflip* ...okay I fell. But it was graceful!",
        "🐼 Ooh, that was a good click! 8/10 technique.",
        "🐼 *spins around* Wheee! 🎉",
        "🐼 I just had a great idea... wait, it's gone.",
        "🐼 *flexes muscles* Check out these gains! 💪",
        "🐼 You know what goes great with clicks? Bamboo! 🎋",
        "🐼 *juggling imaginary bamboo* I'm multitalented!",
        "🐼 Plot twist: I was the texture sorter all along!",
        "🐼 *pretends to be busy* Very important panda business!",
        "🐼 Every click makes me stronger! 🏋️",
        "🐼 I give this click a ⭐⭐⭐⭐⭐ rating!",
        "🐼 *slow clap* Bravo, great clicking form!",
        "🐼 Fun fact: I've been clicked more times than I can count!",
        "🐼 Is it bamboo o'clock yet? 🕐",
        "🐼 *moonwalks* I've been practicing!",
    ]

    # Feed responses
    FEED_RESPONSES = [
        "🎋 *nom nom nom* Delicious bamboo!",
        "🎋 Yummy! More please!",
        "🎋 *happy munching sounds*",
        "🎋 This is the good stuff!",
        "🎋 Best meal ever!",
        "🎋 *panda food dance*",
        "🎋 You know the way to my heart!",
        "🎋 Om nom nom! 😋",
        "🎋 Is this organic? Tastes organic! 🌿",
        "🎋 *chef's kiss* Perfection!",
        "🎋 This beats sorting textures any day!",
        "🎋 My compliments to the chef! 👨‍🍳",
        "🎋 I could eat this all day! Well, I do...",
        "🎋 *burps* Excuse me! More, please!",
        "🎋 Nothing beats fresh bamboo! 💚",
        "🎋 Sharing is caring! ...But this is mine. 😏",
        "🎋 *happy wiggle* Food makes everything better!",
        "🎋 Bamboo: 10/10, would recommend!",
        "🎋 You're officially my favorite person! ❤️",
        "🎋 *munches contentedly* This is the life...",
        "🎋 Did you grow this yourself? It's amazing!",
        "🎋 I'm a simple panda with simple needs: bamboo!",
        "🎋 *saves some for later* Thanks!",
        "🎋 Food always improves my mood! 😊",
        "🎋 You really understand pandas! 🐼💕",
    ]

    # Drag responses
    DRAG_RESPONSES = [
        "🐼 Wheee!",
        "🐼 Where are we going?!",
        "🐼 This is fun!",
        "🐼 Hold on tight!",
        "🐼 I can see my house from here!",
        "🐼 Faster! Faster!",
        "🐼 Warp speed, engage! 🚀",
        "🐼 Is this a rollercoaster?!",
        "🐼 Best. Day. Ever!",
        "🐼 *giggles* This tickles!",
        "🐼 Are we there yet?",
        "🐼 Zoom zoom! 💨",
        "🐼 This is better than bamboo!",
        "🐼 I believe I can fly! Well, glide...",
        "🐼 Panda express coming through! 🚂",
        "🐼 Wheee! Do it again!",
        "🐼 *wind in fur* So exhilarating!",
        "🐼 I'm getting dizzy! In a good way!",
        "🐼 My paws aren't even touching the ground!",
        "🐼 This is my new favorite thing!",
    ]

    # Toss responses
    TOSS_RESPONSES = [
        "🐼 WHEEEEE! 🚀",
        "🐼 I'm flying!",
        "🐼 Was that necessary?!",
        "🐼 Do it again! Do it again!",
        "🐼 I believe I can fly! 🎵",
        "🐼 Panda airlines, departing!",
        "🐼 To infinity and beyond!",
        "🐼 Houston, we have liftoff! 🌙",
        "🐼 *flails adorably* AHHH!",
        "🐼 This wasn't in my job description!",
        "🐼 I'm a bird! I'm a plane! I'm a panda!",
        "🐼 Gravity is just a suggestion!",
        "🐼 *air paws* Look ma, no hands!",
        "🐼 This is either amazing or terrible!",
        "🐼 Next stop: the ceiling!",
        "🐼 I didn't know pandas could fly! 🦅",
        "🐼 Woo-hoo! Best flight ever!",
        "🐼 Coming in for a landing!",
        "🐼 That was both terrifying and awesome!",
        "🐼 Can we do that every day?!",
    ]

    # Wall hit responses
    WALL_HIT_RESPONSES = [
        "🐼 Ouch! 💥",
        "🐼 That's gonna leave a mark!",
        "🐼 Hey, watch it!",
        "🐼 *sees stars* ⭐",
        "🐼 I need a helmet...",
        "🐼 Not the face!",
        "🐼 Ow ow ow! 😵",
        "🐼 That hurt more than my pride!",
        "🐼 *rubs head* Maybe a softer wall next time?",
        "🐼 I meant to do that... *cough*",
        "🐼 The wall started it!",
        "🐼 I'm okay! Just... give me a second...",
        "🐼 Note to self: walls are solid.",
        "🐼 *dazed* What happened?",
        "🐼 I've had worse! ...Maybe not.",
        "🐼 Someone put a wall there!",
        "🐼 *shakes head* Everything's spinning!",
        "🐼 I need ice. And bamboo. Mostly bamboo.",
        "🐼 That wall came out of nowhere!",
        "🐼 *groans* Why do walls have to be so hard?",
    ]

    # Shaking responses
    SHAKE_RESPONSES = [
        "🐼 S-s-stop shaking me!",
        "🐼 M-m-my teeth are chattering!",
        "🐼 I'm a panda, not a maraca!",
        "🐼 E-e-earthquake! Oh wait, that's just you!",
        "🐼 *rattles* I'm falling apart!",
        "🐼 Is this what it feels like in a blender?!",
        "🐼 Everything is blurry! 😵",
        "🐼 My bamboo is going everywhere!",
        "🐼 S-s-seriously?! Again?!",
        "🐼 I need a seatbelt! 🫨",
        "🐼 My brain is scrambled!",
        "🐼 I can hear my thoughts rattling!",
        "🐼 *teeth chattering* C-c-cold? No, just shaken!",
        "🐼 Please... make it stop... 🤢",
        "🐼 I'm NOT a snow globe!",
    ]

    # Spinning responses
    SPIN_RESPONSES = [
        "🐼 I'm getting dizzy! 🌀",
        "🐼 Round and round we go!",
        "🐼 *dizzy eyes* Which way is up?!",
        "🐼 I can see the whole room spinning!",
        "🐼 Wheeeee! ...I'm gonna be sick!",
        "🐼 Stop the ride, I want off! 🎡",
        "🐼 Is this a washing machine?!",
        "🐼 My fur is getting tangled!",
        "🐼 *spinning* I believe I can fly-y-y!",
        "🐼 The world is a carousel! 🌍",
        "🐼 Am I a fidget spinner now?! 🌪️",
        "🐼 Everything looks like a blur!",
        "🐼 Round and round... and round... 😵‍💫",
        "🐼 I see stars! And not the good kind! ⭐",
        "🐼 This is worse than the teacup ride!",
    ]
    
    # Belly poke/jiggle responses
    BELLY_POKE_RESPONSES = [
        "🐼 *belly jiggles* Hehe, that tickles! 🫃",
        "🐼 *wobble wobble* My tummy is so squishy!",
        "🐼 Boing boing! Like a water balloon! 😂",
        "🐼 *jiggles* It's all the bamboo, okay?!",
        "🐼 *belly bounce* Stop poking my tummy! 😊",
        "🐼 *wiggles* I'm not fat, I'm fluffy!",
        "🐼 *jiggle jiggle* That's my bamboo belly!",
        "🐼 *wobbles* Hey! That's my food storage!",
        "🐼 *squish* It's like a panda pillow! 🤗",
        "🐼 *bouncy belly* Too many dumplings... worth it!",
    ]

    # Panda hover thoughts
    HOVER_THOUGHTS = [
        "💭 Thinking about bamboo...",
        "💭 Processing textures is fun!",
        "💭 Wonder what's for lunch...",
        "💭 Is it nap time yet?",
        "💭 These textures look organized!",
        "💭 Should I learn Python?",
        "💭 Life is good.",
        "💭 Texture sorting: 10/10 would recommend",
        "💭 I wonder if other pandas sort textures...",
        "💭 Maybe I should write a blog about this.",
        "💭 Do I look cute from this angle?",
        "💭 What if bamboo was blue instead of green?",
        "💭 I could really go for a nap right now.",
        "💭 Are clouds just sky fluff?",
        "💭 Why is it called a 'texture' anyway?",
        "💭 I'm basically a professional at this point.",
        "💭 Note to self: more snack breaks.",
        "💭 These pixels won't sort themselves!",
        "💭 I wonder what the user is thinking...",
        "💭 Life goals: unlimited bamboo.",
        "💭 Just panda things... 🐼",
        "💭 Maybe I should take up yoga.",
        "💭 I'm pretty good at this job!",
        "💭 Time flies when you're having fun!",
        "💭 Should I get a haircut? Do pandas get haircuts?",
        "💭 *deep thoughts about texture sorting*",
        "💭 I bet I could sort 1000 files in my sleep.",
        "💭 Existential panda thoughts...",
        "💭 Living the dream! Well, a panda's dream.",
        "💭 Wonder what's on the menu tonight...",
    ]
    
    # Petting responses
    PETTING_RESPONSES = [
        "🐼 *purrs* (Wait, pandas don't purr...)",
        "🐼 That feels nice!",
        "🐼 More pets please!",
        "🐼 You're the best!",
        "🐼 *happy panda sounds*",
        "🐼 I could get used to this!",
        "🐼 *leans into pets* Ahhh, perfect!",
        "🐼 You really know how to treat a panda!",
        "🐼 This is my happy place! 😊",
        "🐼 *melts* So relaxing...",
        "🐼 Best. Pets. Ever!",
        "🐼 You have magic hands! ✨",
        "🐼 *closes eyes contentedly* Bliss...",
        "🐼 Don't stop! Please don't stop!",
        "🐼 I'm officially your biggest fan now!",
        "🐼 *tail wags* (Do pandas have tails? Whatever!)",
        "🐼 This beats working any day!",
        "🐼 You're hired as official panda petter!",
        "🐼 *makes happy noises* 🎵",
        "🐼 I could do this all day!",
        "🐼 Petting: approved! ✅",
        "🐼 You found my favorite spot!",
        "🐼 *stretches* That's the good stuff!",
        "🐼 Pure happiness right here! 💚",
        "🐼 You're a natural at this!",
    ]
    
    # Body part interaction responses
    BODY_PART_RESPONSES = {
        'head': [
            "🐼 *enjoys head pats* Ahh, that's the spot!",
            "🐼 My ears are ticklish! 😊",
            "🐼 Head scratches are the best!",
            "🐼 *closes eyes* Pure bliss...",
            "🐼 Right behind the ears! Perfect!",
            "🐼 You're a head-petting pro!",
        ],
        'body': [
            "🐼 *belly wiggles* Hehe, that tickles!",
            "🐼 My tummy is soft, isn't it?",
            "🐼 *happy rumble* More belly rubs!",
            "🐼 You found the fluffy zone!",
            "🐼 *purrs contentedly*",
            "🐼 This panda approves! 👍",
        ],
        'arms': [
            "🐼 Hey, those are my bamboo-grabbing paws!",
            "🐼 *high five* ✋",
            "🐼 Careful with the paws!",
            "🐼 Want a fist bump? 🤜🤛",
            "🐼 My arms are tired from sorting!",
            "🐼 Paw massage? Yes please!",
        ],
        'legs': [
            "🐼 Those are my walking sticks!",
            "🐼 *wiggles toes* Ticklish!",
            "🐼 My legs aren't made for running...",
            "🐼 Foot rub? Don't mind if I do!",
            "🐼 These legs were made for sitting!",
            "🐼 *kicks playfully*",
        ],
        'butt': [
            "🐼 Hey! Watch it! 😳",
            "🐼 That's my sitting cushion!",
            "🐼 *scoots away* Personal space!",
            "🐼 Excuse you! 🙈",
            "🐼 This seat is taken!",
            "🐼 That's a no-touch zone! Well... okay fine.",
        ],
    }
    
    # Clothing/outfit change responses
    CLOTHING_RESPONSES = [
        "👔 Ooh, looking fancy! Do I look good?",
        "👕 *twirls* Fashion panda on the runway!",
        "🎀 This outfit is SO me!",
        "👗 I feel like a whole new panda!",
        "🧥 Cozy AND stylish, perfect combo!",
        "👘 *struts* I was born for fashion!",
        "🤵 Professional panda, at your service!",
        "👑 Dress for the job you want, right?",
        "✨ Mirror mirror on the wall... I look amazing!",
        "🪞 *checks reflection* Not bad, not bad at all!",
    ]

    # Toy interaction responses
    TOY_RESPONSES = [
        "🎾 Yay, playtime! *bounces excitedly*",
        "🎮 Best. Toy. Ever!",
        "🧸 *hugs toy* This is my new favorite!",
        "🎯 Watch this trick! *fumbles*  ...Almost had it!",
        "🪀 I could play with this all day!",
        "🏀 *tosses in air* Wheee!",
        "🎲 Let's play, let's play, let's play!",
        "🧩 Ooh, a challenge! I love puzzles!",
        "🪁 *runs around with toy* This is the best!",
        "🤖 A new friend! Hi there, little buddy!",
    ]

    # Food-specific context responses (more specific than FEED_RESPONSES)
    FOOD_CONTEXT_RESPONSES = [
        "🍱 *eyes light up* Is that for me?!",
        "🍜 *slurp slurp* So tasty!",
        "🍪 Cookies?! You know me so well!",
        "🍰 *does happy food dance* 💃",
        "🌱 Fresh and delicious! *crunch crunch*",
        "😋 My tummy says thank you!",
        "🍃 *carefully picks up food* Ooh, fancy!",
        "🎋 Nothing beats a good meal!",
        "✨ *golden bamboo sparkle* This is legendary!",
        "🐼 *pats belly* Room for one more bite!",
    ]
    
    # Easter egg triggers
    EASTER_EGGS = {
        'konami': '🎮 Up, Up, Down, Down, Left, Right, Left, Right, B, A, Start!',
        'bamboo': '🎋 Unlimited bamboo mode activated!',
        'ninja': '🥷 Stealth sorting engaged!',
        'panda_rage': '💢 PANDA RAGE MODE ACTIVATED! CLICK COUNT: 10!',
        'thousand_files': '🏆 HOLY SH*T! 1000 FILES SORTED! LEGENDARY!',
        'midnight_madness': '🌙 WHY ARE YOU AWAKE AT 3 AM? GO TO SLEEP!',
    }
    
    # Error codes with panda-themed responses
    ERROR_RESPONSES = {
        'E001_FILE_NOT_FOUND': "🐼❌ [E001] File vanished! It pulled a ninja move on us!",
        'E002_PERMISSION_DENIED': "🐼🔒 [E002] Permission denied! Even pandas have access levels!",
        'E003_DISK_FULL': "🐼💾 [E003] Disk full! Too much bamboo data!",
        'E004_CORRUPT_FILE': "🐼💔 [E004] Corrupt file detected! This texture has seen better days...",
        'E005_TIMEOUT': "🐼⏰ [E005] Timed out! Even I don't nap this long!",
        'E006_NETWORK_ERROR': "🐼🌐 [E006] Network error! The bamboo WiFi is down again!",
        'E007_INVALID_FORMAT': "🐼📄 [E007] Invalid format! That's not a texture, that's abstract art!",
        'E008_MEMORY_LOW': "🐼🧠 [E008] Low memory! My brain is full of bamboo recipes!",
        'E009_DUPLICATE_FILE': "🐼👯 [E009] Duplicate detected! Déjà vu, or just lazy sorting?",
        'E010_UNKNOWN': "🐼❓ [E010] Unknown error! Even I don't know what happened!",
        'E011_READ_ERROR': "🐼📖 [E011] Read error! This file is playing hard to get!",
        'E012_WRITE_ERROR': "🐼✍️ [E012] Write error! My paws are too clumsy for this!",
        'E013_CONFIG_ERROR': "🐼⚙️ [E013] Config error! Someone messed with the settings!",
        'E014_SORT_FAILED': "🐼📂 [E014] Sort failed! These textures are unsortable rebels!",
        'E015_AI_ERROR': "🐼🤖 [E015] AI error! Even artificial intelligence needs bamboo breaks!",
    }
    
    # Processing status messages  
    PROCESSING_MESSAGES = [
        "🐼 Sorting textures like a pro!",
        "🐼 Crunching those pixels...",
        "🐼 Analyzing texture patterns...",
        "🐼 Organizing the digital bamboo forest...",
        "🐼 Almost done! ...Maybe.",
        "🐼 Working hard or hardly working?",
        "🐼 *sorts furiously*",
        "🐼 This texture goes here... no, THERE!",
        "🐼 Making order from chaos!",
        "🐼 Your files are in good paws!",
    ]
    
    # Success messages
    SUCCESS_MESSAGES = [
        "🐼✅ Sorted successfully! Bamboo break time!",
        "🐼🎉 All done! That was satisfying!",
        "🐼👏 Great work, team! High-five!",
        "🐼⭐ Perfect sort! Gold star for us!",
        "🐼🏆 Achievement unlocked: Texture Master!",
        "🐼💯 100% sorted! Let's celebrate!",
    ]
    
    # Mood-specific messages
    MOOD_MESSAGES = {
        PandaMood.SARCASTIC: [
            "Oh wow, took you long enough. 🙄",
            "Sure, I'll just wait here. Not like I have bamboo to eat.",
            "Faster? Nah, take your time. I'm immortal apparently.",
            "Oh great, another texture. How exciting. 😒",
            "Wow, you're really going for it today, huh?",
            "I'm so thrilled I could... *yawn*... barely stay awake.",
            "Fantastic. Just fantastic. Really.",
            "Oh, is that what we're doing now? Cool. Cool cool cool.",
            "I'm just HERE for moral support. Obviously.",
            "This is fine. Everything is fine. 🔥",
        ],
        PandaMood.RAGE: [
            "THAT'S IT! I'VE HAD ENOUGH! 💢",
            "WHY DO YOU KEEP FAILING?! 🔥",
            "ANOTHER ERROR?! ARE YOU KIDDING ME?! 😤",
            "I CAN'T TAKE IT ANYMORE! 😡",
            "THIS IS UNACCEPTABLE! 💥",
            "RAGE MODE: FULLY ACTIVATED!",
            "DO I LOOK LIKE I'M JOKING?!",
            "YOU'RE TESTING MY PATIENCE!",
            "BAMBOO WON'T FIX THIS!",
            "I'M A PANDA, NOT A MIRACLE WORKER!",
        ],
        PandaMood.DRUNK: [
            "Heyyy... you're pretty cool, you know that? 🍺",
            "*hiccup* Let's sort some... whatever those things are... 🥴",
            "Everything's... spinning... but in a good way! 🍻",
            "I love you, man... I really do... 🍺",
            "*stumbles* Whoops! The floor moved!",
            "Bamboo tastes... *hiccup*... even better like this!",
            "We should do karaoke! 🎤",
            "Is there two of you or am I seeing double?",
            "*giggles* Everything's so funny! 😂",
            "I'm not drunk, YOU'RE drunk! ...Wait.",
        ],
        PandaMood.EXISTENTIAL: [
            "What is the meaning of sorting textures? 🌌",
            "Are we just... organizing pixels in an infinite void? ✨",
            "10,000 files... and for what? What does it all mean? 💭",
            "Do textures dream of electric pandas?",
            "In the grand scheme of things, does any of this matter?",
            "We're all just stardust sorting stardust...",
            "Is reality just a really well-organized texture pack?",
            "What if WE'RE the textures being sorted?",
            "The universe is so vast, and here I am... sorting.",
            "Maybe the real textures were the friends we made along the way.",
        ],
        PandaMood.HAPPY: [
            "Life is beautiful! 😊",
            "What a wonderful day for sorting!",
            "I'm so happy I could dance! 💃",
            "Everything is awesome! 🎉",
            "Best job ever!",
            "I love texture sorting!",
            "You're doing great! Keep it up!",
            "This is fun! 🎈",
        ],
        PandaMood.EXCITED: [
            "OMG OMG OMG! This is so cool! 🤩",
            "I can't contain my excitement! ⚡",
            "THIS IS AMAZING!",
            "Best thing ever! EVER!",
            "I'M SO PUMPED! 💪",
            "LET'S GOOOOO!",
            "YEAH! That's what I'm talking about!",
            "Can you feel the energy?! ⚡",
        ],
        PandaMood.TIRED: [
            "So... tired... 😮‍💨",
            "Can we take a break? Please?",
            "My paws are exhausted...",
            "*yawns* Need... bamboo... and sleep...",
            "I think I've earned a nap...",
            "How many more textures? 😴",
            "Coffee... need coffee... or bamboo...",
            "Is it bedtime yet?",
        ],
    }
    
    def __init__(self, name: str = "Panda", gender: PandaGender = PandaGender.NON_BINARY):
        """Initialize the panda character.
        
        Args:
            name: The panda's name (default: "Panda")
            gender: The panda's gender (default: NON_BINARY)
        """
        self.name = name
        self.gender = gender
        self.current_mood = PandaMood.HAPPY
        self.click_count = 0
        self.pet_count = 0
        self.feed_count = 0
        self.hover_count = 0
        self.drag_count = 0
        self.toss_count = 0
        self.shake_count = 0
        self.spin_count = 0
        self.toy_interact_count = 0
        self.clothing_change_count = 0
        self.items_thrown_at_count = 0
        self.belly_poke_count = 0
        self.easter_eggs_triggered: Set[str] = set()
        self.start_time = time.time()
        self.files_processed_count = 0
        self.failed_operations = 0
        
        self._lock = threading.RLock()
    
    def set_name(self, name: str):
        """Set the panda's name."""
        with self._lock:
            self.name = name
            logger.info(f"Panda renamed to: {name}")
    
    def set_gender(self, gender: PandaGender):
        """Set the panda's gender."""
        with self._lock:
            self.gender = gender
            logger.info(f"Panda gender set to: {gender.value}")
    
    def get_pronoun_subject(self) -> str:
        """Get subject pronoun (he/she/they) based on gender."""
        with self._lock:
            if self.gender == PandaGender.MALE:
                return "he"
            elif self.gender == PandaGender.FEMALE:
                return "she"
            else:
                return "they"
    
    def get_pronoun_object(self) -> str:
        """Get object pronoun (him/her/them) based on gender."""
        with self._lock:
            if self.gender == PandaGender.MALE:
                return "him"
            elif self.gender == PandaGender.FEMALE:
                return "her"
            else:
                return "them"
    
    def get_pronoun_possessive(self) -> str:
        """Get possessive pronoun (his/her/their) based on gender."""
        with self._lock:
            if self.gender == PandaGender.MALE:
                return "his"
            elif self.gender == PandaGender.FEMALE:
                return "her"
            else:
                return "their"
    
    
    def set_mood(self, mood: PandaMood):
        """Set panda's current mood."""
        with self._lock:
            self.current_mood = mood
            logger.debug(f"Panda mood changed to: {mood.value}")
    
    def get_mood_indicator(self) -> str:
        """Get emoji indicator for current mood."""
        mood_emojis = {
            PandaMood.HAPPY: "😊",
            PandaMood.EXCITED: "🤩",
            PandaMood.WORKING: "💼",
            PandaMood.TIRED: "😮‍💨",
            PandaMood.CELEBRATING: "🎉",
            PandaMood.SLEEPING: "😴",
            PandaMood.SARCASTIC: "🙄",
            PandaMood.RAGE: "😡",
            PandaMood.DRUNK: "🥴",
            PandaMood.EXISTENTIAL: "🤔",
            PandaMood.MOTIVATING: "💪",
            PandaMood.TECH_SUPPORT: "🤓",
            PandaMood.SLEEPY: "🥱",
        }
        return mood_emojis.get(self.current_mood, "🐼")
    
    def get_animation_state(self, animation_name: str = 'idle') -> str:
        """Get a valid animation state name.
        
        Animation rendering is handled by the canvas-drawn panda in
        panda_widget.py. This method validates and returns the state name.
        
        Args:
            animation_name: Requested animation state
            
        Returns:
            A valid animation state name
        """
        if animation_name in self.ANIMATION_STATES:
            return animation_name
        return 'idle'

    def get_animation_frame(self, animation_name: str = 'idle') -> str:
        """Get animation state name for current state.
        
        The panda is rendered on a tkinter canvas. This returns the
        animation state name for the canvas drawing system.
        """
        return self.get_animation_state(animation_name)
    
    def get_animation_frame_sequential(self, animation_name: str = 'idle', frame_index: int = 0) -> str:
        """Get animation state name (frame_index used by canvas renderer).
        
        The panda is rendered on a tkinter canvas which handles frame
        progression internally. This returns the animation state name.
        
        Args:
            animation_name: Name of the animation state
            frame_index: Frame counter (used by canvas renderer)
            
        Returns:
            The animation state name
        """
        return self.get_animation_state(animation_name)
    
    def on_click(self) -> str:
        """Handle panda being clicked."""
        with self._lock:
            self.click_count += 1
            
            # Easter egg: clicks trigger rage
            if self.click_count == self.RAGE_CLICK_THRESHOLD:
                self.easter_eggs_triggered.add('panda_rage')
                self.set_mood(PandaMood.RAGE)
                return self.EASTER_EGGS['panda_rage']
            
            response = random.choice(self.CLICK_RESPONSES)
            # Replace generic panda references with custom name if renamed
            if self.name != "Panda":
                import re
                response = re.sub(r'\bPanda\b', self.name, response)
            return response
    
    def on_hover(self) -> str:
        """Handle mouse hovering over panda."""
        with self._lock:
            self.hover_count += 1
            return random.choice(self.HOVER_THOUGHTS)
    
    def on_pet(self) -> str:
        """Handle panda being petted."""
        with self._lock:
            self.pet_count += 1
            return random.choice(self.PETTING_RESPONSES)
    
    def on_feed(self) -> str:
        """Handle panda being fed."""
        with self._lock:
            self.feed_count += 1
            return random.choice(self.FEED_RESPONSES)

    def on_drag(self) -> str:
        """Handle panda being dragged."""
        self.drag_count += 1
        return random.choice(self.DRAG_RESPONSES)

    def on_toss(self) -> str:
        """Handle panda being tossed."""
        self.toss_count += 1
        return random.choice(self.TOSS_RESPONSES)

    def on_wall_hit(self) -> str:
        """Handle panda hitting a wall."""
        return random.choice(self.WALL_HIT_RESPONSES)

    def on_shake(self) -> str:
        """Handle panda being shaken side to side."""
        self.shake_count += 1
        return random.choice(self.SHAKE_RESPONSES)

    def on_spin(self) -> str:
        """Handle panda being spun in circles."""
        self.spin_count += 1
        return random.choice(self.SPIN_RESPONSES)

    def on_belly_poke(self) -> str:
        """Handle panda's belly being poked (triggers jiggle effect)."""
        self.belly_poke_count += 1
        return random.choice(self.BELLY_POKE_RESPONSES)

    def on_clothing_change(self) -> str:
        """Handle panda changing clothes."""
        self.clothing_change_count += 1
        return random.choice(self.CLOTHING_RESPONSES)

    def on_item_thrown_at(self, item_name: str, body_part: str) -> str:
        """Handle an item being thrown at the panda.
        
        Args:
            item_name: Name of the item thrown
            body_part: Where the item hit ('head', 'body', 'belly', 'legs')
            
        Returns:
            Reaction string
        """
        self.items_thrown_at_count += 1
        if body_part == 'head':
            responses = [
                f"🐼 OW! {item_name} hit me on the head! 💥🤕",
                f"🐼 *BONK* Hey! Who threw {item_name} at my head?! 😠",
                f"🐼 *rubs head* That {item_name} really hurt! 😣",
                f"🐼 *ducks too late* Ow ow ow! My head! 🌟",
                f"🐼 *sees stars* Was that a {item_name}?! 💫",
            ]
        elif body_part in ('body', 'belly'):
            responses = [
                f"🐼 *belly wobbles* Oof! {item_name} got me right in the tummy! 🫃",
                f"🐼 *jiggles* My belly! That {item_name} made it wobble! 😂",
                f"🐼 *catches {item_name} with belly* Look, I'm a goalkeeper! ⚽",
                f"🐼 *belly bounce* Boing! {item_name} bounced off my tummy! 🤣",
                f"🐼 *oof* Right in the belly... at least it's padded! 😅",
            ]
        else:
            responses = [
                f"🐼 *stumbles* {item_name} tripped me up! 😵",
                f"🐼 Hey! Don't throw {item_name} at my feet! 🦶",
                f"🐼 *kicks {item_name} back* Take that! ⚡",
                f"🐼 *dodges... poorly* {item_name} got me! 😆",
            ]
        return random.choice(responses)

    def on_toy_received(self) -> str:
        """Handle panda receiving a toy."""
        return random.choice(self.TOY_RESPONSES)

    def on_food_received(self) -> str:
        """Handle panda receiving food."""
        return random.choice(self.FOOD_CONTEXT_RESPONSES)

    def on_item_interact(self, item_name: str, item_type: str) -> str:
        """Handle panda walking to and interacting with an item on screen.
        
        Args:
            item_name: Name of the item
            item_type: 'toy' or 'food'
            
        Returns:
            Interaction response string
        """
        if item_type == 'food':
            food_actions = [
                f"🐼 *walks over to {item_name}* Ooh, is that food?!",
                f"🐼 *picks up {item_name}* Don't mind if I do! *nom nom*",
                f"🐼 *sniffs {item_name}* Smells amazing! *chomp*",
                f"🐼 *waddles to {item_name}* Snack time! 😋",
                f"🐼 *grabs {item_name}* This is mine now! *munch munch*",
            ]
            self.feed_count += 1
            return random.choice(food_actions)
        else:
            toy_actions = [
                f"🐼 *walks to {item_name}* Oooh, what's this?! *kicks it*",
                f"🐼 *runs to {item_name}* PLAYTIME! *bats it around*",
                f"🐼 *spots {item_name}* Mine! *rolls it across screen*",
                f"🐼 *waddles to {item_name}* Let's play! *pounces*",
                f"🐼 *picks up {item_name}* Watch this trick! *tosses in air*",
            ]
            self.toy_interact_count += 1
            return random.choice(toy_actions)
    
    def get_context_menu(self) -> Dict[str, str]:
        """Get right-click context menu options."""
        return {
            'pet_panda': '🐾 Pet the panda',
            'feed_bamboo': '🎋 Feed bamboo',
            'check_mood': f'{self.get_mood_indicator()} Check mood',
        }
    
    def track_file_processed(self):
        """Track that a file was processed."""
        with self._lock:
            self.files_processed_count += 1
            
            # Easter egg: 1000 files
            if self.files_processed_count == 1000:
                self.easter_eggs_triggered.add('thousand_files')
            
            # Existential crisis after 10k files
            if self.files_processed_count >= 10000:
                self.set_mood(PandaMood.EXISTENTIAL)
    
    def track_operation_failure(self):
        """Track a failed operation."""
        with self._lock:
            self.failed_operations += 1
            
            # Enter rage mode after 5 failures
            if self.failed_operations >= 5:
                self.set_mood(PandaMood.RAGE)
    
    def check_time_for_3am(self) -> bool:
        """Check if it's 3 AM and trigger easter egg."""
        now = datetime.now()
        if now.hour == 3:
            if 'midnight_madness' not in self.easter_eggs_triggered:
                self.easter_eggs_triggered.add('midnight_madness')
                return True
        return False
    
    def handle_text_input(self, text: str) -> bool:
        """
        Handle text input for easter eggs.
        
        Returns:
            True if easter egg triggered
        """
        text_lower = text.lower()
        
        for trigger in ['bamboo', 'ninja', 'konami']:
            if trigger in text_lower and trigger not in self.easter_eggs_triggered:
                self.easter_eggs_triggered.add(trigger)
                return True
        
        return False
    
    def get_statistics(self) -> Dict:
        """Get panda statistics."""
        return {
            'name': self.name,
            'gender': self.gender.value,
            'current_mood': self.current_mood.value,
            'click_count': self.click_count,
            'pet_count': self.pet_count,
            'feed_count': self.feed_count,
            'hover_count': self.hover_count,
            'drag_count': self.drag_count,
            'toss_count': self.toss_count,
            'shake_count': self.shake_count,
            'spin_count': self.spin_count,
            'toy_interact_count': self.toy_interact_count,
            'clothing_change_count': self.clothing_change_count,
            'items_thrown_at_count': self.items_thrown_at_count,
            'belly_poke_count': self.belly_poke_count,
            'files_processed': self.files_processed_count,
            'failed_operations': self.failed_operations,
            'easter_eggs_found': len(self.easter_eggs_triggered),
            'easter_eggs': list(self.easter_eggs_triggered),
            'uptime_seconds': time.time() - self.start_time,
        }
    
    def get_error_response(self, error_code: str = None) -> str:
        """Get a panda-themed error response.
        
        Args:
            error_code: Specific error code (e.g., 'E001_FILE_NOT_FOUND'),
                       or None for random error response
                       
        Returns:
            Panda-themed error message string
        """
        if error_code and error_code in self.ERROR_RESPONSES:
            return self.ERROR_RESPONSES[error_code]
        return random.choice(list(self.ERROR_RESPONSES.values()))
    
    def get_processing_message(self) -> str:
        """Get a panda-themed processing status message."""
        return random.choice(self.PROCESSING_MESSAGES)
    
    def get_success_message(self) -> str:
        """Get a panda-themed success message."""
        return random.choice(self.SUCCESS_MESSAGES)
    
    def get_mood_message(self) -> str:
        """Get a message appropriate for the current mood.
        
        Returns:
            A mood-specific message, or a generic happy message
        """
        with self._lock:
            messages = self.MOOD_MESSAGES.get(self.current_mood, self.MOOD_MESSAGES[PandaMood.HAPPY])
            return random.choice(messages)
    
    def update_mood_from_context(self, files_processed: int = 0, errors: int = 0, 
                                  idle_time_seconds: float = 0):
        """Automatically update mood based on current context.
        
        Args:
            files_processed: Number of files just processed
            errors: Number of recent errors
            idle_time_seconds: How long the user has been idle
        """
        with self._lock:
            if errors >= 5:
                self.set_mood(PandaMood.RAGE)
            elif errors >= 2:
                self.set_mood(PandaMood.SARCASTIC)
            elif idle_time_seconds > 600:  # 10 minutes idle
                self.set_mood(PandaMood.SLEEPING)
            elif idle_time_seconds > 300:  # 5 minutes idle
                self.set_mood(PandaMood.SLEEPY)
            elif files_processed > 100:
                self.set_mood(PandaMood.TIRED)
            elif files_processed > 50:
                self.set_mood(PandaMood.WORKING)
            elif files_processed > 0:
                self.set_mood(PandaMood.HAPPY)
            # If nothing triggers, keep current mood
    
    def get_body_part_at_position(self, rel_y: float) -> str:
        """Determine which body part is at a relative y position.
        
        The panda is drawn with body-shaped canvas rendering,
        roughly divided into regions:
        - head: top 25% (ears, eyes)
        - body: 25-50% (nose, mouth, torso)
        - arms: same as body region but used for side clicks
        - butt: 50-75% (lower torso)
        - legs: bottom 25% (feet)
        
        Args:
            rel_y: Relative Y position (0.0 = top, 1.0 = bottom)
            
        Returns:
            Body part name string
        """
        if rel_y < self.HEAD_BOUNDARY:
            return 'head'
        elif rel_y < self.BODY_BOUNDARY:
            return 'body'
        elif rel_y < self.BUTT_BOUNDARY:
            return 'butt'
        else:
            return 'legs'
    
    def on_body_part_click(self, body_part: str) -> str:
        """Handle click on a specific body part.
        
        Args:
            body_part: Name of body part ('head', 'body', 'arms', 'legs', 'butt')
            
        Returns:
            Response message string
        """
        with self._lock:
            self.click_count += 1
            responses = self.BODY_PART_RESPONSES.get(body_part, self.CLICK_RESPONSES)
            return random.choice(responses)
    
    def on_rub(self, body_part: str = 'body') -> str:
        """Handle being rubbed/petted on a body part.
        
        Args:
            body_part: Where the panda is being rubbed
            
        Returns:
            Response message string
        """
        with self._lock:
            self.pet_count += 1
            responses = self.BODY_PART_RESPONSES.get(body_part, self.PETTING_RESPONSES)
            return random.choice(responses)
