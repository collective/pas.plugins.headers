# -*- coding: utf-8 -*-
from plone import api
from Products.Five import BrowserView
from six.moves.urllib import parse


# List taken over from browser/login/login.py in CMFPlone 5.2.
LOGIN_TEMPLATE_IDS = set([
    'localhost',
    'logged-out',
    'logged_in',
    'login',
    'login_failed',
    'login_form',
    'login_password',
    'login_success',
    'logout',
    'mail_password',
    'mail_password_form',
    'member_search_results',
    'pwreset_finish',
    'passwordreset',
    'register',
    'registered',
    'require_login',
    # Extra for us:
    'headerlogin',
])


class HeaderLogin(BrowserView):

    def get_came_from(self):
        came_from = self.request.get('came_from', None)
        if not came_from:
            came_from = self.request.get('HTTP_REFERER', None)
            if not came_from:
                return
        url_tool = api.portal.get_tool('portal_url')
        if not url_tool.isURLInPortal(came_from):
            return
        came_from_path = parse.urlparse(came_from)[2].split('/')
        for login_template_id in LOGIN_TEMPLATE_IDS:
            if login_template_id in came_from_path:
                return
        return came_from

    def __call__(self):
        if api.user.is_anonymous():
            # Return a message, to avoid infinite redirects.
            return "ERROR: headerlogin failed"
        url = self.get_came_from()
        if url:
            portal_url = api.portal.get_tool('portal_url')
            if not portal_url.isURLInPortal(url):
                url = None
        if not url:
            nav_root = api.portal.get_navigation_root(self.context)
            url = nav_root.absolute_url()
        self.request.response.redirect(url)
