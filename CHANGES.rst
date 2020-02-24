Changelog
=========


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
