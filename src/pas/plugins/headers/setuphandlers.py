# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import INonInstallable
from zope.interface import implementer

import logging


logger = logging.getLogger(__name__)


@implementer(INonInstallable)
class HiddenProfiles(object):

    def getNonInstallableProfiles(self):  # pragma: no cover
        """Hide uninstall profile from site-creation and quickinstaller."""
        return [
            'pas.plugins.headers:uninstall',
        ]


def post_install(context):
    """Post install script"""
    # Setup our request header plugin.
    pas = getToolByName(context, 'acl_users')
    plugin_id = 'request_headers'

    # Create plugin if it does not exist.
    from pas.plugins.headers.plugins import HeaderPlugin
    if plugin_id not in pas.objectIds():
        plugin = HeaderPlugin(
            title='Request Headers',
        )
        plugin.id = plugin_id
        pas._setObject(plugin_id, plugin)
        logger.info('Created %s in acl_users.', plugin_id)
    plugin = getattr(pas, plugin_id)
    if not isinstance(plugin, HeaderPlugin):
        raise ValueError(
            'Existing PAS plugin {0} is not a HeaderPlugin.'.format(plugin_id))

    # Activate all supported interfaces for this plugin.
    activate = []
    plugins = pas.plugins
    for info in plugins.listPluginTypeInfo():
        interface = info['interface']
        interface_name = info['id']
        if plugin.testImplements(interface):
            activate.append(interface_name)
            logger.info(
                'Activating interface %s for plugin %s',
                interface_name, info['title'])

    plugin.manage_activateInterfaces(activate)
    logger.info('Plugins activated.')

    # Order some plugins to make sure our plugin is at the top.
    # This is not needed for all plugin interfaces.
    for info in plugins.listPluginTypeInfo():
        interface_name = info['id']
        if interface_name in ['IChallengePlugin', 'IPropertiesPlugin']:
            iface = plugins._getInterfaceFromName(interface_name)
            for obj in plugins.listPlugins(iface):
                plugins.movePluginsUp(iface, [plugin_id])
            logger.info('Moved %s to top of %s.', plugin_id, interface_name)


def uninstall(context):
    """Uninstall script"""
    pas = getToolByName(context, 'acl_users')
    plugin_id = 'request_headers'

    # Remove plugin if it exists.
    if plugin_id not in pas.objectIds():
        return
    from pas.plugins.headers.plugins import HeaderPlugin
    plugin = getattr(pas, plugin_id)
    if not isinstance(plugin, HeaderPlugin):
        logger.warning(
            'PAS plugin %s not removed: it is not a HeaderPlugin.', plugin_id)
        return
    pas._delObject(plugin_id)
    logger.info('Removed HeaderPlugin %s from acl_users.', plugin_id)
