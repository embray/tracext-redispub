"""Wiki event handling."""

from __future__ import absolute_import


from trac.core import implements
from trac.wiki.api import IWikiChangeListener

from .redis import RedisComponent
from .util import dumps


class RedisWikiStream(RedisComponent):
    """
    Listens for wiki creation/change/deletion events and and publishes
    them to the relevant channels:

        * Wiki page creation events are published to the
          ``<prefix>.<env>.wiki.created`` channel, where ``<prefix>`` is the
          configurable channel name prefix (e.g. 'trac'), and ``<env>`` is the
          environment name.

          Messages on this channel are JSON-encoded dictionaries representing
          the wiki page (``"version"`` is always ``1`` for new pages)::

              {
                  "name": "PageName",
                  "version": 1,
                  "time": "2018-03-02T12:31:28.184283",
                  "author": "somebody",
                  "text": "...full page text...",
                  "comment": "edit comment, if any",
                  "readonly": 0
              }

        * Wiki change events are published to the
          ``<prefix>.<env>.wiki.changed.<name>`` channel, where ``<prefix>``
          and ``<env>`` are as before, and ``<name>`` is the wiki page name.  This
          allows subscribing just to the changes on a specific wiki page, if
          desired.  The message is a JSON-encoded dictionary with the same
          format as the wiki created event, along with an additional
          ``"old_text"`` property containing the previous text of the wiki page
          before the change::

              {
                  "name": "PageName",
                  "version": 2,
                  ...
                  "text": "the new text of the page",
                  "old_text": "the old text of the page",
                  ...
              }

        * Wiki deletion events are published to the
          ``<prefix>.<env>.wiki.deleted`` channel.  These events have the same
          format as wiki creation events, and include the properties of the
          just-deleted wiki page..
    """

    implements(IWikiChangeListener)

    _realm = 'wiki'

    # ITicketChangeListener methods
    def wiki_page_added(self, page):
        self.redis.publish(self._channel_name('created'),
                           self._page_to_json(page))

    def wiki_page_changed(self, page, version, t, comment, author, ipnr=None):
        # note: the version, timestamp (t), comment, and author arguments
        # are all passed to this method for backwards-compatibility, but the
        # same data is already available in the page object
        self.redis.publish(self._channel_name('changed', page.name),
                           self._page_to_json(page, old_text=True))

    def wiki_page_deleted(self, ticket):
        self.redis.publish(self._channel_name('deleted'),
                           self._page_to_json(page))

    def _channel_name(self, method, page_name=None):
        channel = super(RedisWikiStream, self)._channel_name(method)
        if page_name is not None:
            channel += '.' + page_name
        return channel

    def _page_to_json(self, page, old_text=False):
        """
        Convert a `trac.wiki.model.WikiPage` object to a JSONified dictionary.
        """
        attrs = ['name', 'version', 'time', 'author', 'text', 'comment',
                 'readonly']

        if old_text:
            attrs.append('old_text')

        return dumps(dict((attr, getattr(page, attr)) for attr in attrs))
