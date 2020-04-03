Changelog
=========


1.3.1 (2020-04-03)
------------------

- Python 3: when ``redirect_url`` unexpectedly is bytes, turn it into native string before comparing.
  [maurits]

- Fixed problem with ``redirect_url`` not starting with a slash.
  With ``headerlogin`` as value we would redirect to http://localhost:8080/Ploneheaderlogin.
  [maurits]


1.3.0 (2020-03-26)
------------------

- We require ``six>=1.12.0`` because we use ``ensure_str``.
  Note that Plone 4.3 and 5.1 currently pin older versions.
  [maurits]

- Fixed NotFound error when redirect_url started with a slash, for example ``/headerlogin``.
  In local development it would redirect to /headerlogin on the Zope root, where it does not exist.
  We now always treat the redirect_url as relative to the Plone site root, unless it is a full url.
  [maurits]

- Fixed exportimport to always set native strings.
  On Python 3 we were setting bytes, which was wrong.
  Fixed same problem in member properties.
  [maurits]


1.2.0 (2020-02-24)
------------------

- Add ``came_from`` query parameter when the challenge plugin redirects.
  [maurits]

- Added ``headerlogin`` page.
  This redirects to the ``came_from`` query parameter or the referer or the navigation root.
  You can use this in the ``redirect_url`` option, and have your frontend server force SAML or CAS login on it.
  When a user arrives on this page and is still anonymous, then apparently SAML/CAS has not worked.
  We then redirect to the standard login page.
  Care is taken to avoid a redirect loop between the login and headerlogin pages.
  [maurits]

- Added option ``create_ticket``.  When reading headers, this checks if Plone knows this user.
  If so, we create an authentication ticket (``__ac`` cookie) with ``plone.session``.
  Then you could let your frontend server only set the headers for some urls, instead of for all.
  Note that this does not work for root Zope users, and it does not take over properties and roles.
  See `issue 6 <https://github.com/collective/pas.plugins.headers/issues/6>`_.
  [maurits]


1.1.0 (2020-02-19)
------------------

- Added Plone 5.2, Python 3 compatibility.  [maurits]


1.0.1 (2019-11-01)
------------------

- Replaced import of ``Globals``, which is gone in Plone 5.2.  [maurits]


1.0.0 (2019-04-25)
------------------

- Make final release, no changes.  [maurits]


1.0.0a2 (2018-08-03)
--------------------

- Documented our ``GenericSetup`` import step.
  Unlike most importers, this reads a ``json`` file, called ``pas.plugins.headers.json``.
  [maurits]


1.0.0a1 (2018-08-03)
--------------------

- Initial release.
  [maurits]
