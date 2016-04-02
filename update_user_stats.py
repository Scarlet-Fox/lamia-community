from woe import sqla
from woe.sqlmodels import *
import woe.sqlmodels as sqlm
from sqlalchemy.orm.attributes import flag_modified
from woe.parsers import emoticon_codes
from woe.utilities import strip_tags

for user in User.query.filter_by(banned=False, validated=True).all():
    def update_user_smileys(user):
        user_name = user.login_name

        # try:
        post_count = sqla.session.query(sqlm.Post) \
            .join(sqlm.Post.topic) \
            .join(sqlm.Topic.category) \
            .filter(sqlm.Post.hidden==False, sqlm.Post.author==user) \
            .filter(sqlm.Category.slug != "welcome-mat").count()
        # except:
        #     sqla.session.rollback()
        #     return

        if post_count < 10:
            return

        posts = list(sqla.session.query(sqlm.Post) \
            .join(sqlm.Post.topic) \
            .join(sqlm.Topic.category) \
            .filter(sqlm.Post.hidden==False, sqlm.Post.author==user) \
            .all())

        emote_frequency = {}
        emotes = []

        for post in posts:
            for emote in emoticon_codes.keys():
                if emote in post.html:
                    if emote_frequency.has_key(emote):
                        emote_frequency[emote] += 1
                    else:
                        emote_frequency[emote] = 1

        emotes = emote_frequency.keys()
        emotes = sorted(emotes, key=lambda x: emote_frequency[x], reverse=True)

        favorite_emotes = emotes

        user = sqlm.User.query.filter_by(login_name=user_name)[0]
        if user.data == None:
            user.data = {}

        new_data = user.data.copy()
        new_data["favorite_emotes"] = favorite_emotes
        user.data = new_data

        user.smileys_last_updated = arrow.utcnow().datetime.replace(tzinfo=None)

        flag_modified(user, "data")
        sqla.session.add(user)
        sqla.session.commit()

    def update_user_last_phrase(user):
        user_name = user.login_name

        # try:
        post_count = sqla.session.query(sqlm.Post) \
            .join(sqlm.Post.topic) \
            .join(sqlm.Topic.category) \
            .filter(sqlm.Post.hidden==False, sqlm.Post.author==user) \
            .filter(sqlm.Category.slug != "welcome-mat").count()
        # except:
        #     sqla.session.rollback()
        #     return

        if post_count < 10:
            return

        posts = list(sqla.session.query(sqlm.Post) \
            .join(sqlm.Post.topic) \
            .join(sqlm.Topic.category) \
            .filter(sqlm.Post.hidden==False, sqlm.Post.author==user) \
            .filter(sqlm.Category.slug != "welcome-mat") \
            .filter(sqlm.Category.slug != "art-show") \
            .all())

        phrase_frequency = {}
        phrases = []
        phrase_length = 6

        for post in posts:
            words = strip_tags(post.html)
            phrases_in_post = range(len(words)-phrase_length)
            post_phrases = {}

            for i_phrase in phrases_in_post:
                word_1 = words[i_phrase].lower().strip()
                word_2 = words[i_phrase+1].lower().strip()
                word_3 = words[i_phrase+2].lower().strip()
                word_4 = words[i_phrase+3].lower().strip()
                word_5 = words[i_phrase+4].lower().strip()
                word_6 = words[i_phrase+5].lower().strip()

                if word_1 == word_2 == word_3 == word_4 == word_5 == word_6:
                    continue

                phrase = unicode(word_1)+" "+unicode(word_2)+" "+unicode(word_3)+" "+unicode(word_4)+" "+unicode(word_5)+" "+unicode(word_6)
                phrase_check = [word_1, word_2, word_3, word_4, word_5, word_6]
                if "don" in phrase_check and "t" in phrase_check:
                    continue
                if "have" in phrase_check and "idea" in phrase_check:
                    continue
                if "youtube" in phrase_check:
                    continue
                if "url" in phrase_check:
                    continue
                if "com" in phrase_check:
                    continue
                if "cdn" in phrase_check:
                    continue
                if "vine" in phrase_check:
                    continue
                if "list" in phrase_check:
                    continue

                if post_phrases.has_key(phrase):
                    continue
                else:
                    post_phrases[phrase] = 1

                if phrase_frequency.has_key(phrase):
                    phrase_frequency[phrase] += 1
                else:
                    phrase_frequency[phrase] = 1

        phrases = phrase_frequency.keys()
        phrases = sorted(phrases, key=lambda x: phrase_frequency[x], reverse=True)

        favorite_phrase = phrases

        user = sqlm.User.query.filter_by(login_name=user_name)[0]
        if user.data == None:
            user.data = {}

        new_data = user.data.copy()
        new_data["favorite_phrase"] = favorite_phrase
        user.data = new_data

        user.phrase_last_updated = arrow.utcnow().datetime.replace(tzinfo=None)

        flag_modified(user, "data")
        sqla.session.add(user)
        sqla.session.commit()

    update_user_smileys(user)
    update_user_last_phrase(user)
