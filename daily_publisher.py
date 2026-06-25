import os
import json
import glob
import random
import requests
import shutil
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Import upload functions
try:
    from upload.upload_instagram import upload_to_instagram
    from upload.upload_threads import upload_to_threads
    from upload.upload_facebook import upload_to_facebook, upload_to_facebook_story
    from upload.upload_to_youtube import upload_to_youtube
except ImportError as e:
    print(f"Error importing upload modules: {e}")
    # Still want to proceed or stop?
    pass

PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"

def get_already_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def get_repost_counts():
    """Count how many times each video has been posted."""
    published = get_already_published()
    counts = {}
    for entry in published:
        vname = entry.get("video_name", "")
        counts[vname] = counts.get(vname, 0) + 1
    return counts

def mark_as_published(video_name, metadata):
    published = get_already_published()
    published.append({
        "video_name": video_name,
        "metadata": metadata
    })
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(published, f, indent=4)

def select_video(specific_video=None):
    published = [item["video_name"] for item in get_already_published()]
    all_videos = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.mp4")))

    if specific_video:
        # specific_video might be a full path or just a filename
        if os.path.exists(specific_video):
            # It's a full path
            vid_path = specific_video
            name = os.path.basename(specific_video)
        else:
            # It's just a filename, join with PROCESSED_DIR
            vid_path = os.path.join(PROCESSED_DIR, specific_video)
            name = specific_video

        if os.path.exists(vid_path):
            if name in published:
                post_count = sum(1 for p in published if p == name)
                print(f"🔄 Video {name} was already published ({post_count}x) - Re-publishing (recycling)")
            return vid_path, name
        else:
            print(f"❌ Error: Specific video {name} not found")
            return None, None

    # Find unpublished videos first
    unpublished = [(vid, os.path.basename(vid)) for vid in all_videos if os.path.basename(vid) not in published]

    if unpublished:
        vid, name = unpublished[0]
        return vid, name

    # All videos published - use weighted random selection (less posted = more likely)
    if all_videos:
        repost_counts = get_repost_counts()
        weights = []
        for vid in all_videos:
            name = os.path.basename(vid)
            count = repost_counts.get(name, 0)
            weight = max(1, 1000 // (3 ** min(count, 6)))
            weights.append(weight)

        selected_vid = random.choices(all_videos, weights=weights, k=1)[0]
        name = os.path.basename(selected_vid)
        post_count = repost_counts.get(name, 0)
        print(f"🎲 All videos published. Weighted random reuse (posted {post_count}x): {name}")
        return selected_vid, name

    return None, None

def generate_caption():
    import random
    import time

    api_key = os.getenv("POLLINATIONS_API_KEY")
    model = os.getenv("AI_MODEL", "openai")

    fallback_titles = [
        "Learn English in 60 Seconds! 🇺🇸 Common Mistakes",
        "Stop Saying 'Very' - Use These Words Instead",
        "English Pronunciation Hack You NEED to Know",
        "Daily English Phrases You'll Actually Use",
        "Grammar Tip: When to Use 'A' vs 'An'",
        "How to Sound More Natural in English",
        "English Vocabulary for Beginners - Part 1",
        "The Most Confusing English Words Explained",
        "Speak English Like a Native - 3 Tips",
        "Common English Mistakes Even Advanced Learners Make",
        "English Idioms You Should Know",
        "Prepositions Made Easy: In, On, At",
        "English Conversation Practice - At the Restaurant",
        "Improve Your English Accent in 1 Minute",
        "Understand Native English Speakers Faster",
    ]

    fallback_descriptions = [
        "Did you know there's a better way to say 'very good'? In this lesson, English with Roxy breaks down the most overused English words and gives you stronger alternatives. Start sounding more fluent today with just one small change. Like if this helped you! 🇺🇸 #englishlearning #learnenglish #englishvocabulary #englishwithroxy #esl #englishlesson #speakenglish #englishgrammar #englishtips #vocabulary #fluentenglish #englishshorts",
        "Stop making this common English mistake! 🛑 Many learners confuse 'affect' and 'effect' — but don't worry, English with Roxy is here to make it crystal clear. Watch till the end for a simple trick to remember the difference. Comment below with a sentence using one of these words! ✍️ #englishlesson #learnenglish #englishgrammar #englishwithroxy #esl #commonmistakes #englishvocabulary #grammartips #speakenglish #studyenglish",
        "Want to sound more like a native English speaker? 🌟 In this short lesson, English with Roxy shares 3 easy pronunciation tips that will transform your speaking instantly. Practice these every day and you'll notice a huge difference. Save this video for later practice! 📌 #englishpronunciation #learnenglish #speakenglish #englishwithroxy #esl #pronunciationtips #englishlesson #americanenglish #accenttraining #fluentenglish",
        "English phrasal verbs can be confusing — but English with Roxy makes them simple! 🤓 Today we're learning 5 phrasal verbs you can use in daily conversation. 'Wake up', 'get along', 'look for'... do you know them all? Test yourself in the comments! ⬇️ #phrasalverbs #englishlesson #learnenglish #englishwithroxy #esl #englishvocabulary #speakenglish #englishgrammar #dailyenglish #englishtips",
        "Can you say these 10 English words correctly? 🗣️ English with Roxy challenges you to pronounce these tricky words. Words like 'vegetable', 'comfortable', and 'literally' — try saying them out loud! How many did you get right? Tell me in the comments! 👇 #englishpronunciation #learnenglish #englishchallenge #englishwithroxy #esl #trickywords #speakenglish #pronunciation #accent #englishtips",
        "The secret to English fluency? Consistency! 📅 English with Roxy shares her best tips for building a daily English learning habit that actually sticks. No boring textbooks, just real practice you can do anywhere. Start today and see results in 30 days! Like if you're committed to learning English! 💪 #englishfluency #learnenglish #englishwithroxy #esl #studyenglish #englishhabits #speakenglish #englishlesson #learningtips #motivation",
        "Prepositions IN, ON, AT — when do you use each? 🤔 This is one of the most confusing topics in English grammar, but English with Roxy explains it in under 60 seconds. Watch this and never mix them up again! Save and share with a friend who's learning English too! 📚 #englishgrammar #prepositions #learnenglish #englishwithroxy #esl #grammartips #englishlesson #speakenglish #studyenglish #englishtips",
        "British vs American English — do you know the differences? 🇬🇧🇺🇸 English with Roxy compares 10 words that are completely different depending on where you are. Which version do you prefer? Tell me in the comments! ⬇️ #britishenglish #americanenglish #learnenglish #englishwithroxy #esl #englishvocabulary #speakenglish #englishteacher #languages #vocabulary",
        "Don't say 'I am agree' ❌ — this is a VERY common mistake! English with Roxy corrects the top 5 grammar errors that even advanced students make. Watch until the end to see if you've been making these mistakes too! Save this for later study! 📖 #commonmistakes #englishgrammar #learnenglish #englishwithroxy #esl #englishlesson #speakenglish #studyenglish #englishtips #grammar",
        "Learn English idioms that natives use every day! 🗣️ English with Roxy teaches you 5 popular idioms like 'break the ice', 'hit the nail on the head', and more. These will make your English sound much more natural and impressive. Try using one in a sentence below! ✨ #englishidioms #learnenglish #englishwithroxy #esl #englishvocabulary #speakenglish #idioms #englishlesson #fluentenglish #nativespeaker",
        "Can you hear the difference between 'ship' and 'sheep'? 🐑 English with Roxy shows you how to master the long and short vowel sounds in English. This is crucial for being understood clearly. Practice with me and repeat out loud! 🔁 #englishpronunciation #vowelsounds #learnenglish #englishwithroxy #esl #speakenglish #pronunciation #minimalpairs #englishlesson #accenttraining",
        "Today's English lesson is all about greetings! 👋 Did you know there are at least 10 different ways to say 'hello' in English? English with Roxy teaches you formal and informal greetings so you can sound natural in any situation. Which one is your favorite? Comment below! 💬 #englishgreetings #learnenglish #englishwithroxy #esl #englishlesson #speakenglish #dailyenglish #conversation #englishtips",
        "Are you using 'since' and 'for' correctly? 🤔 This is one of the most confusing grammar points for English learners. English with Roxy breaks it down with simple examples you'll remember forever. Watch now and master this once and for all! Save for later! ✅ #englishgrammar #sincevfor #learnenglish #englishwithroxy #esl #grammartips #englishlesson #speakenglish #studyenglish #englishtips",
        "Expand your vocabulary with English with Roxy! 📖 Today's word is 'exquisite' — a beautiful word to describe something extremely beautiful or delicate. Learn its meaning, pronunciation, and how to use it in a sentence. Try making your own sentence in the comments! ⬇️ #vocabularybuilding #learnenglish #englishwithroxy #esl #englishwords #speakenglish #englishlesson #wordoftheday #fluentenglish",
        "The quickest way to improve your English listening skills? 🎧 English with Roxy shares her top 5 methods for understanding native speakers better. From podcasts to movie techniques, these tips will level up your comprehension fast. Like if you find this useful! 👍 #englishlistening #learnenglish #englishwithroxy #esl #listeningtips #speakenglish #englishlesson #comprehension #studyenglish #fluency",
    ]

    if not api_key:
        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        print("Warning: POLLINATIONS_API_KEY not found. Using fallback captions.")
        return chosen_title, chosen_desc

    vibes = [
        "clear and encouraging — explain like a patient and friendly teacher",
        "fun and energetic — make learning English exciting and enjoyable",
        "simple and practical — give tips learners can use right away",
        "supportive and motivating — help learners feel confident and capable",
        "engaging and interactive — ask questions and get learners thinking",
        "warm and approachable — make learners feel comfortable and welcome",
        "quick and actionable — deliver value in under 60 seconds",
    ]
    chosen_vibe = random.choice(vibes)

    prompt = (
        f"Write a completely unique, long, and captivating title and description for a short video "
        f"for the social media page 'English with Roxy'. "
        f"The page teaches English to learners around the world — covering grammar, vocabulary, pronunciation, common mistakes, idioms, and everyday conversation tips. "
        f"It's clear, supportive, and makes learning English fun and accessible. "
        f"Speak as a friendly and experienced English teacher who genuinely wants to help students improve. "
        f"Make the vibe {chosen_vibe}. "
        f"The description should be LONG (4-6 sentences minimum), educational yet engaging. "
        f"Include engagement calls-to-action such as: "
        f"- Like if this helped you learn something new! "
        f"- Comment with your example sentence! "
        f"- Share with a friend who's learning English! "
        f"- Follow English with Roxy for more daily lessons! "
        f"Include relevant hashtags in ALL LOWERCASE such as #englishlearning #learnenglish #englishwithroxy #esl #englishlesson #speakenglish #englishgrammar #englishvocabulary #englishtips #studyenglish #fluentenglish #englishpronunciation. "
        f"Return ONLY a valid JSON object in this format: {{\"title\": \"<title>\", \"description\": \"<description>\"}} "
        f"Do not include any other text or markdown block backticks."
    )

    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "seed": random.randint(1, 999999)
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

        content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)

        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        return result.get("title", chosen_title), result.get("description", chosen_desc)
    except Exception as e:
        print(f"Error generating caption: {e}")
        return random.choice(fallback_titles), random.choice(fallback_descriptions)

def main():
    print("=" * 60)
    print("🚀 DAILY AUTOMATION STARTING")
    print("=" * 60)
    
    specific_video = sys.argv[1] if len(sys.argv) > 1 else None
    video_path, video_name = select_video(specific_video)
    if not video_path:
        print("✅ No new videos found to publish. Exiting.")
        return
        
    print(f"👉 Selected Video: {video_name}")
    print("🧠 Generating caption via Pollination AI...")
    title, description = generate_caption()
    
    print(f"📝 Title: {title}")
    print(f"📝 Description:\n{description}")
    
    # Combined caption for platforms that use a single text field
    combined_caption = f"{title}\n\n{description}"
    
    success_flags = {
        "instagram_reel": False,
        "instagram_story": False,
        "facebook_reel": False,
        "facebook_story": False,
        "threads": False,
        "youtube": False
    }
    
    # Instagram Reels
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=False)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_reel"] = True
    except Exception as e:
        print(f"❌ Instagram Reel upload failed: {e}")
        
    # Instagram Stories
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=True)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_story"] = True
    except Exception as e:
        print(f"❌ Instagram Story upload failed: {e}")
        
    # Facebook Reels
    try:
        result = upload_to_facebook(video_path, description, title=title)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_reel"] = True
    except Exception as e:
        print(f"❌ Facebook Reel upload failed: {e}")
        
    # Facebook Stories
    try:
        result = upload_to_facebook_story(video_path)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_story"] = True
    except Exception as e:
        print(f"❌ Facebook Story upload failed: {e}")
        
    # Threads
    try:
        result = upload_to_threads(video_path, combined_caption)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Threads: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["threads"] = True
    except Exception as e:
        print(f"❌ Threads upload failed: {e}")
        
    # YouTube Shorts
    try:
        upload_to_youtube(video_path, title, description, tags=["englishlearning", "learnenglish", "englishwithroxy", "esl", "englishlesson", "speakenglish", "englishgrammar", "englishvocabulary", "englishtips", "studyenglish", "fluentenglish", "englishpronunciation", "englishshorts", "englishclass"])
        success_flags["youtube"] = True
    except Exception as e:
        print(f"❌ YouTube upload failed: {e}")
        
    # Record as published regardless of partial success,
    # to avoid repeating the same video. Alternatively, only record if fully successful.
    print("\n✅ Marking video as published.")
    
    # Check if this is a recycled video (already in published_videos.json)
    published_list = get_already_published()
    is_recycled = any(item["video_name"] == video_name for item in published_list)
    
    if is_recycled:
        print(f"   🔄 This is a recycled video (re-publishing)")
    
    mark_as_published(video_name, {
        "title": title,
        "description": description,
        "success_flags": success_flags,
        "recycled": is_recycled
    })
    
    # Move the published video to Published_Videos folder
    published_dir = "Published_Videos"
    if not os.path.exists(published_dir):
        os.makedirs(published_dir)
        
    try:
        dest_path = os.path.join(published_dir, video_name)
        shutil.move(video_path, dest_path)
        print(f"📦 Moved published video to {dest_path}")
    except Exception as e:
        print(f"❌ Failed to move published video: {e}")
    
    print("🎉 DAILY AUTOMATION COMPLETE")

if __name__ == "__main__":
    main()
