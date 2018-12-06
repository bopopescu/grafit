import uuid
from datetime import datetime

from textblob import TextBlob

from django.contrib.auth.models import AbstractUser
from django.db import models
from neomodel import StructuredNode, StringProperty, UniqueIdProperty, Relationship, StructuredRel, FloatProperty, DateTimeProperty
from django.db.models import signals
from django.dispatch import receiver
from django.db import connection

import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return self.username


class Workspace(models.Model):
    name = models.CharField(max_length=250)
    initials = models.CharField(max_length=2)
    users = models.ManyToManyField(User)


class Article(models.Model):
    title = models.CharField(max_length=250)
    text = models.TextField(blank=True)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def related(self):
        relatedNodes = []
        try:
            relatedGraphNodes = GraphArticle.nodes.get(uid=self.id).related
            for node in relatedGraphNodes:
                relatedNodes.append({
                    "id": int(node.uid),
                    "title": node.name
                })
        except:
            # article node does not exist yet
            pass

        return relatedNodes

    @property
    def shorttext(self):
        blob = TextBlob(self.text)
        firstTwoSentences = " ".join([str(s) for s in blob.sentences[:3]])
        if len(firstTwoSentences) > 400:
            return self.text[:400].rsplit(' ', 1)[0] + " [...]"
        else:
            return firstTwoSentences

    def __unicode__(self):
        return '{"title": %s, "title" %s}' % (self.id, self.title)


@receiver([signals.post_save, signals.post_delete], sender=Article, dispatch_uid="update_search_index")
def update_search_index(sender, instance, **kwargs):
    logger.info("update search index")
    cursor = connection.cursor()
    cursor.execute(
        'REFRESH MATERIALIZED VIEW CONCURRENTLY grafit_search_index;')
    logger.info("finished updating search index")

@receiver([signals.post_save, signals.post_delete], sender=Article, dispatch_uid="update_search_word")
def update_search_word(sender, instance, **kwargs):
    logger.info("update search word")
    cursor = connection.cursor()
    cursor.execute(
        'REFRESH MATERIALIZED VIEW CONCURRENTLY grafit_search_word;')
    logger.info("finished updating search word")


class ArticleRel(StructuredRel):
    created_at = DateTimeProperty(
        default=lambda: datetime.now()
    )
    tf_idf = FloatProperty()


class GraphArticle(StructuredNode):
    uid = UniqueIdProperty()
    name = StringProperty()
    related = Relationship('GraphArticle', 'RELATED', model=ArticleRel)


class SearchResult(models.Model):
    id = models.BigIntegerField(primary_key=True)
    title = models.TextField()
    headline = models.TextField()
    rank = models.DecimalField(max_digits=19, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'search_index'


class SearchWord(models.Model):
    word = models.TextField(primary_key=True)
    similarity = models.DecimalField(max_digits=19, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'search_word'
