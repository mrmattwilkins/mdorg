import frontmatter

from django.db import models
from django.utils import timezone

# Create your models here.


class Tag(models.Model):
    """A string that can be attached to an item.

    Attributes
    ----------
    name : str
        The name of the tag

    """

    name = models.CharField(max_length=100)

class Item(models.Model):
    """The markdown item

    Attributes
    ----------

    title : str
        The title in the markdown file

    created : datetime
        When created (can be specified in head of markdown)

    accessed: datetime
        Last accessed

    tags: 
        A many to many relationship with tags

    content:

    path:
        Path to file on disk that this item represents

    """

    title = models.CharField(max_length=100)
    created = models.DateTimeField()
    accessed = models.DateTimeField(blank=True, null=True)
    tags = models.ManyToManyField(Tag)
    path = models.CharField(max_length=200)

    @classmethod
    def create(cls, filename):
        """Return a new Item

        Parameters
        ----------
        filename : str
            The full path of markdown file

        Returns
        -------
        Item
            The new Item
        """

        with open(filename) as f:
            text = frontmatter.load(f)

        if 'title' not in text:
            raise ValueError(f"No title in {filename}")
            
        item = cls(
            title=text['title'],
            path=filename
        )

        if 'date' in text:
            item.created = text['date']
        if 'accessed' in text:
            item.accessed = text['accessed']

        tags = []
        if 'tags' in text:
            tags = [
                Tag.objects.get_or_create(name=tag)[0]
                for tag in text['tags'].split()
            ]

        return (item, tags)


