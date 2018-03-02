Trac Redis Pub
==============
`Trac <https://trac.edgewall.org/>`_ plugin providing `Redis pub/sub
channels <https://redis.io/topics/pubsub>`_ for Trac events, specifically
ticket and wiki page creation/updates.

This can be used to implement services external to the Trac web server
itself that react to events on a Trac project.  For example, one can provide
a stream of ticket events like:

.. code:: python

    >>> import redis
    >>> client = redis.Redis()
    >>> pubsub = client.pubsub()
    >>> for event in pubsub.listen():
    ...     print(event)
    ...
    {'pattern': None, 'type': 'psubscribe', 'channel': 'trac.*', 'data': 1L}
    {'pattern': 'trac.*', 'type': 'pmessage', 'channel': 'trac.test.wiki.created', 'data': '{"comment": "Change comment", "name": "NewWikiPage", "author": "anonymous", "text": "Page contents.", "readonly": 0, "version": 1, "time": "2018-03-02T14:10:22.844985+00:00"}'}
    {'pattern': 'trac.*', 'type': 'pmessage', 'channel': 'trac.test.wiki.changed.NewWikiPage', 'data': '{"comment": "Editing page.", "name": "NewWikiPage", "author": "anonymous", "text": "Page contents.\\r\\nAdditional contents.", "old_text": "Page contents.", "readonly": 0, "version": 2, "time": "2018-03-02T14:10:36.192988+00:00"}'}
    {'pattern': 'trac.*', 'type': 'pmessage', 'channel': 'trac.test.ticket.created', 'data': '{"status": "new", "changetime": "2018-03-02T14:15:01.401989+00:00", "reporter": "anonymous", "cc": "", "milestone": "", "component": "component1", "keywords": "", "owner": "somebody", "id": 17, "description": "Problem description.", "author": "", "summary": "Test ticket", "priority": "major", "version": "", "time": "2018-03-02T14:15:01.401989+00:00", "type": "defect"}'}
    {'pattern': 'trac.*', 'type': 'pmessage', 'channel': 'trac.test.ticket.changed.17', 'data': '{"comment": "Updated milestone.", "new_values": {"milestone": "milestone1"}, "id": 17, "old_values": {"milestone": ""}, "author": "anonymous"}'}
    

.. note::

    Version 0.1 supports basic ticket and wiki-related events.  However,
    there are many other types of events in Trac that could be monitored
    this way, for which support may be added in future versions in the
    remote chance there is any demand.


Available Channels
------------------

The following channels can be subscribed to:

Ticket channels
^^^^^^^^^^^^^^^

* Ticket creation events are published to the
  ``<prefix>.<env>.ticket.created`` channel, where ``<prefix>`` is the
  configurable channel name prefix (e.g. 'trac'), and ``<env>`` is the
  environment name.

  Messages on this channel consist of the field values of the created ticket
  (along with the ticket ID) as a JSON-encoded dictionary:

  .. code:: json
  
      {
          "id": 1,
          "summary": "...",
          "description": "...",
          ...
      }

* Ticket change events are published to the
  ``<prefix>.<env>.ticket.changed.<id>`` channel, where ``<prefix>`` and
  ``<env>`` are as before, and ``<id>`` is the ticket ID.  This allows
  subscribing just to the changes on a specific ticket, if desired.  The
  message is a JSON-encoded dictionary with the following format:

  .. code:: json
  
      {
          "id": 1,
          "new_values": { ... },
          "old_values": { ... },
          "author": "somebody",
          "comment": "A comment..."
      }

  Where ``"id"`` is the ticket ID. If the values of any ticket fields where
  changed, ``"new_values"`` maps field names to their new values, and
  ``"old_values"`` maps field names to the previous values of fields that
  changed.  ``"author"`` is the author of the change, and ``"comment"`` is
  the comment associated with the change (which may be blank).

* Ticket deltion events are published to the
  ``<prefix>.<env>.ticket.deleted`` channel.  These events have the same
  format as ticket creation events, and include the values of all the fields
  on the just-deleted ticket.

Wiki channels
-------------

* Wiki page creation events are published to the
  ``<prefix>.<env>.wiki.created`` channel, where ``<prefix>`` is the
  configurable channel name prefix (e.g. 'trac'), and ``<env>`` is the
  environment name.

  Messages on this channel are JSON-encoded dictionaries representing the
  wiki page (``"version"`` is always ``1`` for new pages):

  .. code:: json

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
  ``<prefix>.<env>.wiki.changed.<name>`` channel, where ``<prefix>`` and
  ``<env>`` are as before, and ``<name>`` is the wiki page name.  This
  allows subscribing just to the changes on a specific wiki page, if
  desired.  The message is a JSON-encoded dictionary with the same format as
  the wiki created event, along with an additional ``"old_text"`` property
  containing the previous text of the wiki page before the change:
  
  .. code:: json

      {
          "name": "PageName",
          "version": 2,
          ...
          "text": "the new text of the page",
          "old_text": "the old text of the page",
          ...
      }

* Wiki deltion events are published to the ``<prefix>.<env>.wiki.deleted``
  channel.  These events have the same format as wiki creation events, and
  include the properties of the just-deleted wiki page..

