import MySQLdb

db=MySQLdb.connect(user="root",db="stream")
cursor = db.cursor()




langCache = {}
def setLanguageId(language):
    if language.name not in langCache:
        cursor.execute("SELECT id from language WHERE name=%s", (language.name))
        result = cursor.fetchone()
        if not result:
            cursor.execute("INSERT INTO language (name) VALUES (%s)", (language.name))
            result = cursor.execute("SELECT id from language WHERE name=%s", (language.name))
            id = int(cursor.lastrowid)
        else:
            id = int(result[0])
        langCache[language.name] = id
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

    for media in medias:
        # INSERT media
        media.pageId = page.id
        cursor.execute("INSERT INTO media (name, img, url, year, pageId) VALUES (%s, %s, %s, %s, %s)", (media.name, media.img, media.url, media.year, media.pageId))
        media.id = int(cursor.lastrowid)

        for tag in media.tags:
            # insert tag and relation
            setTagId(tag)
            cursor.execute("INSERT IGNORE INTO media_to_tag (mediaId, tagId) VALUES (%s, %s)", (media.id, tag.id))

        for part in media.getSubs():
            # insert part
            part.pageId = media.pageId
            part.mediaId = media.id
            cursor.execute("INSERT INTO media_part (name, num, mediaId, pageId) VALUES (%s, %s, %s, %s)", (part.name, part.num, part.mediaId, part.pageId))
            part.id = int(cursor.lastrowid)

            for alternative in part.getSubs():
                # insert alternative
                alternative.pageId = part.pageId
                alternative.partId = part.id
                if alternative.language:
                    setLanguageId(alternative.language)
                    alternative.languageId = alternative.language.id
                if alternative.subtitle:
                    setLanguageId(alternative.subtitle)
                    alternative.subtitleId = alternative.subtitle.id
                cursor.execute("INSERT INTO media_alternative (name, hoster, partId, pageId, subtitleId, languageId) VALUES (%s, %s, %s, %s, %s, %s)", (alternative.name, alternative.hoster, alternative.partId,
                    alternative.pageId, alternative.subtitleId, alternative.languageId))
                alternative.id = int(cursor.lastrowid)
                for altPart in alternative.getSubs():
                    # insert alternative part
                    altPart.pageId = alternative.pageId
                    altPart.alternativeId = alternative.id
                    cursor.execute("INSERT INTO media_alternative_part (name, url, num, alternativeId, pageId) VALUES (%s, %s, %s, %s, %s)", (altPart.name, altPart.url, altPart.num, altPart.alternativeId, altPart.pageId))
                    altPart.id = int(cursor.lastrowid)
                    for flv in altPart.getSubs():
                        # insert flv
                        flv.pageId = altPart.pageId
                        flv.alternativePartId = altPart.id
                        cursor.execute("INSERT INTO media_flv (link, code, type, data, available, alternativePartId, pageId) VALUES (%s, %s, %s, %s, %s, %s, %s)", (flv.link, flv.code, flv.type, flv.data,
                            flv.available, flv.alternativePartId, flv.pageId))
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