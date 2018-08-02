# -*- coding: utf-8 -*-
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer

import pas.plugins.headers


class PasPluginsHeadersLayer(PloneSandboxLayer):

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        self.loadZCML(package=pas.plugins.headers)
        self.loadZCML(package=pas.plugins.headers.tests)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'pas.plugins.headers:default')


PAS_PLUGINS_HEADERS_FIXTURE = PasPluginsHeadersLayer()


PAS_PLUGINS_HEADERS_INTEGRATION_TESTING = IntegrationTesting(
    bases=(PAS_PLUGINS_HEADERS_FIXTURE,),
    name='PasPluginsHeadersLayer:IntegrationTesting',
)


PAS_PLUGINS_HEADERS_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(PAS_PLUGINS_HEADERS_FIXTURE,),
    name='PasPluginsHeadersLayer:FunctionalTesting',
)
