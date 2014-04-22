import MySQLdb
import sys
import logging

log = logging.getLogger(__name__)


db=MySQLdb.connect(user="root",db="stream")
cursor = db.cursor()


langCache = {}
def setLanguageId(language):
    if language.name not in langCache:
        from tools.page import Language
        cursor.execute("DELETE FROM language")
        for id in Language.idToLanguages:
            name = Language.idToLanguages[id]
            cursor.execute("INSERT IGNORE INTO language (id, name) VALUES (%s, %s)", (id, name))
            langCache[name] = id
    language.id = langCache[language.name]

tagCache = {}
def setTagId(tag):
    if tag.name not in tagCache:
        cursor.execute("SELECT id from tag WHERE name=%s", (tag.name))
        result = cursor.fetchone()
        if not result:
            cursor.execute("INSERT INTO tag (name) VALUES (%s)", (tag.name))
            result = cursor.execute("SELECT id from tag WHERE name=%s", (tag.name))
            id = int(cursor.lastrowid)
        else:
            id = int(result[0])
        tagCache[tag.name] = id
    tag.id = tagCache[tag.name]

def persist(page, medias):
    # INSERT page
    cursor.execute("INSERT IGNORE INTO page (name, url) VALUES (%s, %s)", (page.name, page.url))
    cursor.execute("SELECT id from page WHERE name=%s", (page.name))
    page.id = int(cursor.fetchone()[0])
    for i in ('media', 'media_part', 'media_alternative', 'media_alternative_part', 'media_flv'):
        cursor.execute("DELETE FROM "+i+" WHERE pageId=%s", (page.id))

    count = 0
    maxCount = len(medias)
    for media in medias:
        count += 1
        sys.stdout.write("Inserting media %d of %d \r" % (count, maxCount))
        sys.stdout.flush()
        # INSERT media
        cursor.execute("INSERT INTO media (name, img, url, year, pageId, length, views, rating, thumbs) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
           (media.name, media.img, media.url, media.year, page.id, media.length, media.views, float(media.rating), ";;".join(media.thumbs)))
        media.id = int(cursor.lastrowid)

        for tag in media.tags:
            # insert tag and relation
            setTagId(tag)
            cursor.execute("INSERT IGNORE INTO media_to_tag (mediaId, tagId) VALUES (%s, %s)", (media.id, tag.id))

        for part in media.getSubs():
            # insert part
            cursor.execute("INSERT INTO media_part (name, season, num, mediaId, pageId) VALUES (%s, %s, %s, %s, %s)", (part.name, part.season, part.num, part.mediaId, page.id))
            part.id = int(cursor.lastrowid)

            for alternative in part.getSubs():
                # insert alternative
                if alternative.language:
                    setLanguageId(alternative.language)
                    alternative.languageId = alternative.language.id
                if alternative.subtitle:
                    setLanguageId(alternative.subtitle)
                    alternative.subtitleId = alternative.subtitle.id
                cursor.execute("INSERT INTO media_alternative (name, hoster, partId, pageId, subtitleId, languageId) VALUES (%s, %s, %s, %s, %s, %s)", (alternative.name, alternative.hoster, alternative.partId,
                    page.id, alternative.subtitleId, alternative.languageId))
                alternative.id = int(cursor.lastrowid)
                for altPart in alternative.getSubs():
                    # insert alternative part
                    cursor.execute("INSERT INTO media_alternative_part (name, url, num, alternativeId, pageId) VALUES (%s, %s, %s, %s, %s)", (altPart.name, altPart.url, altPart.num, altPart.alternativeId, page.id))
                    altPart.id = int(cursor.lastrowid)
                    for flv in altPart.getSubs():
                        # insert flv
                        cursor.execute("INSERT INTO media_flv (link, code, type, data, available, alternativePartId, pageId) VALUES (%s, %s, %s, %s, %s, %s, %s)", (flv.link, flv.code, flv.type, flv.data,
                            flv.available, flv.alternativePartId, page.id))
                        flv.id = int(cursor.lastrowid)




def recreate():
    cursor.execute("""
DROP TABLE IF EXISTS `language`;
CREATE TABLE `language` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `media`;
CREATE TABLE `media` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `img` varchar(255) DEFAULT NULL,
  `url` varchar(255) DEFAULT NULL,
  `year` int(11) DEFAULT NULL,
  `pageId` int(11) DEFAULT NULL,
  `length` int(5) DEFAULT NULL,
  `views` int(9) DEFAULT NULL,
  `rating` float DEFAULT NULL,
  `thumbs` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `pageId` (`pageId`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `media_alternative`;
CREATE TABLE `media_alternative` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `hoster` text,
  `partId` int(11) DEFAULT NULL,
  `pageId` int(11) DEFAULT NULL,
  `subtitleId` int(11) DEFAULT NULL,
  `languageId` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `partId` (`partId`),
  KEY `pageId` (`pageId`),
  KEY `subtitleId` (`subtitleId`),
  KEY `languageId` (`languageId`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `media_alternative_part`;
CREATE TABLE `media_alternative_part` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `url` varchar(255) DEFAULT NULL,
  `num` varchar(255) DEFAULT NULL,
  `alternativeId` int(11) DEFAULT NULL,
  `pageId` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `alternativeId` (`alternativeId`),
  KEY `pageId` (`pageId`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `media_flv`;
CREATE TABLE `media_flv` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `link` varchar(255) DEFAULT NULL,
  `code` varchar(255) DEFAULT NULL,
  `type` varchar(255) DEFAULT NULL,
  `data` text,
  `available` tinyint(1) DEFAULT NULL,
  `alternativePartId` int(11) DEFAULT NULL,
  `pageId` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `alternativePartId` (`alternativePartId`),
  KEY `pageId` (`pageId`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `media_languages`;
CREATE TABLE `media_languages` (
  `mediaId` int(11) DEFAULT NULL,
  `languageId` int(11) DEFAULT NULL,
  KEY `mediaId` (`mediaId`),
  KEY `languageId` (`languageId`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `media_part`;
CREATE TABLE `media_part` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `season` int(11) DEFAULT NULL,
  `num` varchar(255) DEFAULT NULL,
  `mediaId` int(11) DEFAULT NULL,
  `pageId` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `mediaId` (`mediaId`),
  KEY `pageId` (`pageId`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `media_subtitles`;
CREATE TABLE `media_subtitles` (
  `mediaId` int(11) DEFAULT NULL,
  `languageId` int(11) DEFAULT NULL,
  KEY `mediaId` (`mediaId`),
  KEY `languageId` (`languageId`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

DROP TABLE IF EXISTS `media_to_tag`;
CREATE TABLE `media_to_tag` (
  `mediaId` int(11) DEFAULT NULL,
  `tagId` int(11) DEFAULT NULL,
  KEY `mediaId` (`mediaId`),
  KEY `tagId` (`tagId`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `page`;
CREATE TABLE `page` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `url` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `url` (`url`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `tag`;
CREATE TABLE `tag` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
    """)
