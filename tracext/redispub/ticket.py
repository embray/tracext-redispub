"""Ticket event handling."""

from __future__ import absolute_import


from trac.core import implements
from trac.ticket.api import ITicketChangeListener

from .redis import RedisComponent
from .util import dumps


class RedisTicketStream(RedisComponent):
    """
    Listens for ticket creation/change/deletion events and and publishes
    them to the relevant channels:

        * Ticket creation events are published to the
          ``<prefix>.<env>.ticket.created`` channel, where ``<prefix>`` is the
          configurable channel name prefix (e.g. 'trac'), and ``<env>`` is the
          environment name.

          Messages on this channel consist of the field values of the created
          ticket (along with the ticket ID) as a JSON-encoded dictionary::

              {
                  "id": 1,
                  "summary": "...",
                  "description": "...",
                  ...
              }

        * Ticket change events are published to the
          ``<prefix>.<env>.ticket.changed.<id>`` channel, where ``<prefix>``
          and ``<env>`` are as before, and ``<id>`` is the ticket ID.  This
          allows subscribing just to the changes on a specific ticket, if
          desired.  The message is a JSON-encoded dictionary with the following
          format::

              {
                  "id": 1,
                  "new_values": { ... },
                  "old_values": { ... },
                  "author": "somebody",
                  "comment": "A comment..."
              }

          Where ``"id"`` is the ticket ID. If the values of any ticket fields
          where changed, ``"new_values"`` maps field names to their new values,
          and ``"old_values"`` maps field names to the previous values of
          fields that changed.  ``"author"`` is the author of the change, and
          ``"comment"`` is the comment associated with the change (which may be
          blank).

        * Ticket deltion events are published to the
          ``<prefix>.<env>.ticket.deleted`` channel.  These events have the
          same format as ticket creation events, and include the values of all
          the fields on the just-deleted ticket.
    """

    implements(ITicketChangeListener)

    _realm = 'ticket'

    # ITicketChangeListener methods
    def ticket_created(self, ticket):
        data = dict(ticket.values)
        data['id'] = ticket.id
        self.redis.publish(self._channel_name('created'), dumps(data))

    def ticket_changed(self, ticket, comment, author, old_values):
        data = {
            'new_values': dict((field, ticket.values.get(field, ''))
                               for field in old_values),
            'old_values': old_values,
            'author': author,
            'comment': comment,
            'id': ticket.id,
        }
        self.redis.publish(self._channel_name('changed', ticket.id),
                           dumps(data))

    def ticket_deleted(self, ticket):
        data = dict(ticket.values)
        data['id'] = ticket.id
        self.redis.publish(self._channel('deleted'), dumps(data))

    def _channel_name(self, method, ticket_id=None):
        channel = super(RedisTicketStream, self)._channel_name(method)
        if ticket_id is not None:
            channel += '.' + str(ticket_id)
        return channel
