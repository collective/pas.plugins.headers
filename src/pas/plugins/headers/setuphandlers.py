from pas.plugins.headers.plugins import HeaderPlugin
from pas.plugins.headers.utils import PLUGIN_ID
from plone.base.interfaces import INonInstallable
from Products.CMFCore.utils import getToolByName
from zope.interface import implementer

import logging


logger = logging.getLogger(__name__)


@implementer(INonInstallable)
class HiddenProfiles:
    def getNonInstallableProfiles(self):  # pragma: no cover
        """Hide uninstall profile from site-creation and quickinstaller."""
        return [
            "pas.plugins.headers:uninstall",
        ]


def post_install(context):
    """Post install script"""
    # Setup our request header plugin.
    pas = getToolByName(context, "acl_users")

    # Create plugin if it does not exist.
    if PLUGIN_ID not in pas.objectIds():
        plugin = HeaderPlugin(
            title="Request Headers",
        )
        plugin.id = PLUGIN_ID
        pas._setObject(PLUGIN_ID, plugin)
        logger.info("Created %s in acl_users.", PLUGIN_ID)
    plugin = getattr(pas, PLUGIN_ID)
    if not isinstance(plugin, HeaderPlugin):
        raise ValueError(f"Existing PAS plugin {PLUGIN_ID} is not a HeaderPlugin.")

    # Activate all supported interfaces for this plugin.
    activate = []
    plugins = pas.plugins
    for info in plugins.listPluginTypeInfo():
        interface = info["interface"]
        interface_name = info["id"]
        if plugin.testImplements(interface):
            activate.append(interface_name)
            logger.info(
                "Activating interface %s for plugin %s", interface_name, info["title"]
            )

    plugin.manage_activateInterfaces(activate)
    logger.info("Plugins activated.")

    # Order some plugins to make sure our plugin is at the top.
    # This is not needed for all plugin interfaces.
    for info in plugins.listPluginTypeInfo():
        interface_name = info["id"]
        if interface_name in ["IChallengePlugin", "IPropertiesPlugin"]:
            iface = plugins._getInterfaceFromName(interface_name)
            for obj in plugins.listPlugins(iface):
                plugins.movePluginsUp(iface, [PLUGIN_ID])
            logger.info("Moved %s to top of %s.", PLUGIN_ID, interface_name)


def uninstall(context):
    """Uninstall script"""
    from pas.plugins.headers.utils import PLUGIN_ID

    pas = getToolByName(context, "acl_users")

    # Remove plugin if it exists.
    if PLUGIN_ID not in pas.objectIds():
        return
    from pas.plugins.headers.plugins import HeaderPlugin

    plugin = getattr(pas, PLUGIN_ID)
    if not isinstance(plugin, HeaderPlugin):
        logger.warning(
            "PAS plugin %s not removed: it is not a HeaderPlugin.", PLUGIN_ID
        )
        return
    pas._delObject(PLUGIN_ID)
    logger.info("Removed HeaderPlugin %s from acl_users.", PLUGIN_ID)


def activate_plugin_type(context, plugin_type):
    """Activate the plugin_type for our plugin.

    plugin_type is an interface.
    """
    pas = getToolByName(context, "acl_users")
    if PLUGIN_ID not in pas.objectIds():
        logger.warning("%s is not in acl_users", PLUGIN_ID)
        return
    plugin = getattr(pas, PLUGIN_ID)
    if not isinstance(plugin, HeaderPlugin):
        logger.warning("Existing PAS plugin %s is not a HeaderPlugin.", PLUGIN_ID)
        return

    # Activate the plugin type.
    plugins = pas.plugins
    plugin_type_name = plugin_type.__name__
    ids = plugins.listPluginIds(plugin_type)
    if PLUGIN_ID not in ids:
        plugins.activatePlugin(plugin_type, PLUGIN_ID)
        logger.info("%s plugin activated.", plugin_type_name)
    else:
        logger.info("%s plugin was already activated.", plugin_type_name)


def activate_credentials_reset_plugin(context):
    from Products.PluggableAuthService.interfaces.plugins import ICredentialsResetPlugin

    activate_plugin_type(context, ICredentialsResetPlugin)
